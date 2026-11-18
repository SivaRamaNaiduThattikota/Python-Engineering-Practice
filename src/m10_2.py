from lesson import *

lesson(
    id="m10-2", num="10.2", title="Context managers",
    intro="The `with` statement pairs setup with guaranteed cleanup. What `with` does step by step, writing context "
          "managers as classes with `__enter__` and `__exit__`, deciding whether to suppress exceptions, the "
          "`contextlib.contextmanager` shortcut and its `try`/`finally` rule, several managers at once and their exit "
          "order, and reentrant managers. Applied to timers, temporary settings, atomic writes, transactions and tracing spans.",
    desc="`with`, `__enter__` and `__exit__`, `contextlib.contextmanager`.",
    keys="context manager with statement __enter__ __exit__ exception suppress contextlib contextmanager yield try finally cleanup resource timer atomic write transaction commit rollback span nested exit order reentrant",
)

term("Context manager", "An object used with `with`: its `__enter__` runs at the start of the block and its `__exit__` always runs at the end, even on errors.")
term("Suppressing an exception", "When `__exit__` returns a true value, the exception raised in the `with` block is swallowed and execution continues after the block.")
term("contextlib.contextmanager", "A decorator that turns a generator with one `yield` into a context manager: code before the `yield` is setup, code after it is cleanup.")

section("why", "Setup and guaranteed cleanup",
    p("""Many operations come in pairs: open a file and close it; acquire a lock and release it; start a timer and stop it; begin a transaction
    and commit or roll back; change a setting and restore it. The second half must happen **even if the work in between fails**, or you leak
    file handles, deadlock other threads, leave half-written data or keep a temporary setting forever. Lesson 7.1 showed the tool for that,
    `try`/`finally`; a **context manager** packages the pair once so every user gets it right with one line: `with open(path) as f:`."""),
    ex("""
    import os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "log.txt")

    f = open(path, "w", encoding="utf-8")      # by hand: easy to forget the finally
    try:
        f.write("first\\n")
    finally:
        f.close()

    with open(path, "a", encoding="utf-8") as f:    # the same guarantee, built in
        f.write("second\\n")
    print(f.closed, open(path, encoding="utf-8").read().splitlines())

    try:
        with open(path, encoding="utf-8") as f:
            raise ValueError("failed while reading")
    except ValueError:
        print("file closed anyway:", f.closed)
    """, "why_with.py"),
)

section("steps", "What `with` does, step by step",
    p("""`with EXPR as name: BODY` runs these steps. Python evaluates `EXPR`, which gives the **context manager** object. It calls the manager's
    `__enter__()` method and binds the **return value** of `__enter__` to `name` (not the manager itself, unless `__enter__` returns
    `self`). It runs the body. Then, however the body ends (normally, with `return`, `break` or an exception), it calls
    `__exit__(exc_type, exc_value, traceback)`. If the body finished without an exception, the three arguments are `None`. If an exception
    occurred, they describe it, and the return value of `__exit__` decides what happens: a **true** value suppresses the exception, so
    execution continues after the `with`; anything else (including `None`, the default return) lets it propagate."""),
    ex("""
    class Show:
        def __init__(self, name, suppress=False):
            self.name, self.suppress = name, suppress

        def __enter__(self):
            print(f"  enter {self.name}")
            return f"resource:{self.name}"         # this is what `as` receives

        def __exit__(self, exc_type, exc, tb):
            print(f"  exit {self.name}, exception={exc_type.__name__ if exc_type else None}")
            return self.suppress

    with Show("a") as r:
        print("  body got", r)

    with Show("b", suppress=True):
        raise KeyError("swallowed")
    print("after b: continued")

    try:
        with Show("c"):
            raise KeyError("propagates")
    except KeyError:
        print("after c: caught outside")
    """, "with_steps.py"),
    p("""The `as` target is whatever `__enter__` returns: for `open`, the file object (which is also the manager); for a lock, `True`; for a
    database transaction, often a connection or cursor. `__exit__` is guaranteed to run once `__enter__` has succeeded; if `__enter__`
    itself raises, the body never runs and `__exit__` is not called, which is why `__enter__` should acquire the resource as its last
    step."""),
)

section("class", "Writing a context manager class",
    p("""A class with `__enter__` and `__exit__` is a context manager. `__enter__` does the setup and returns whatever the block should use,
    very often `self`, so the block can read results from the manager later. `__exit__` does the cleanup and, in nearly all cases, returns
    `False` or nothing, so exceptions continue to the caller after the cleanup has happened. Returning `True` swallows **every** exception
    from the block, including bugs, so a manager should suppress only specific, intended exception types, as `contextlib.suppress` does
    (problem 3)."""),
    ex("""
    import time

    class Timer:
        def __init__(self, clock=time.perf_counter):
            self.clock = clock
            self.elapsed = None

        def __enter__(self):
            self.start = self.clock()
            return self

        def __exit__(self, exc_type, exc, tb):
            self.elapsed = self.clock() - self.start
            return False                        # never hide errors

    ticks = iter([10.0, 10.25, 20.0, 21.5])
    with Timer(lambda: next(ticks)) as t:
        pass
    print(t.elapsed)
    try:
        with Timer(lambda: next(ticks)) as t2:
            raise TimeoutError("model too slow")
    except TimeoutError:
        print("timed the failure too:", t2.elapsed)
    """, "class_manager.py"),
    p("""The timer records the duration in `__exit__`, so slow failures are measured as well as successes, which matters for latency dashboards
    (8.3). Context managers that should react to errors can inspect `exc_type` in `__exit__`: a transaction commits when it is `None` and
    rolls back otherwise; a tracing span marks itself as failed; a test helper checks that an expected error occurred (`pytest.raises` is a
    context manager, 13.1)."""),
)

section("generator", "`contextlib.contextmanager`: a generator with one yield",
    p("""Writing a class is verbose for simple pairs. The decorator `contextlib.contextmanager` turns a **generator function** with exactly one
    `yield` into a context manager. The code before `yield` is the setup (`__enter__`), the value yielded is what `as` receives, and the code
    after `yield` is the cleanup (`__exit__`). If the `with` body raises, the exception is **re-raised inside the generator, at the `yield`**.
    So the cleanup must sit in a `finally` block around the `yield`; otherwise an error in the body skips it entirely (problem 6)."""),
    ex("""
    from contextlib import contextmanager

    @contextmanager
    def temporary(obj, **changes):
        old = {k: getattr(obj, k) for k in changes}
        for k, v in changes.items():
            setattr(obj, k, v)
        try:
            yield obj
        finally:
            for k, v in old.items():
                setattr(obj, k, v)

    class Settings:
        temperature = 0.2
        model = "small"

    s = Settings()
    with temporary(s, temperature=0.9) as cfg:
        print("inside:", cfg.temperature, cfg.model)
    print("after:", s.temperature)
    try:
        with temporary(s, model="large"):
            raise RuntimeError("request failed")
    except RuntimeError:
        print("restored after error:", s.model)
    """, "contextmanager.py"),
    p("""To react to the exception instead of just cleaning up, catch it around the `yield`: `except SomeError: ...` lets you log it, and then either
    `raise` (propagate) or not (suppress). As with classes, suppress only on purpose. A `@contextmanager` function can also be used as a
    **decorator** above another function, `@temporary(s, temperature=0)`, which wraps every call of that function in the block (a fresh
    generator is created per call). But a manager **object** obtained by calling it, `cm = temporary(s, ...)`, is single-use: its generator can
    run only once, so each `with` needs a fresh call (problem 16)."""),
)

section("several", "Several managers, nesting and exit order",
    p("""One `with` statement can open several managers, separated by commas; since Python 3.10 they can be wrapped in parentheses across lines.
    They are entered **left to right** and exited in **reverse** order, like nested `with` blocks, so a resource acquired later (a cursor) is
    released before one acquired earlier (its connection). If one of them fails to enter, those already entered are exited properly."""),
    ex("""
    from contextlib import contextmanager

    log = []

    @contextmanager
    def step(name):
        log.append(f"enter {name}")
        try:
            yield name
        finally:
            log.append(f"exit {name}")

    with (
        step("connection") as conn,
        step("transaction") as tx,
        step("cursor") as cur,
    ):
        log.append(f"work with {conn}, {tx}, {cur}")
    print(log)
    """, "several.py"),
    p("""Context managers also compose with everything else in this course: a decorator (8.1) can wrap a function body in a `with` block; a
    generator (6.3) can hold a `with` open while it yields, keeping a file open exactly as long as the stream is consumed; and when the number
    of managers is only known at run time (open N files), `contextlib.ExitStack` collects them dynamically (10.3)."""),
)

section("reentrant", "Single-use, reusable and reentrant managers",
    p("""Context managers differ in whether one object can be used more than once. **Single-use** managers work in one `with` only: file objects
    (once closed, they stay closed) and every `@contextmanager` object. **Reusable** managers can be used in several consecutive `with`
    blocks, like a `Timer` instance that resets on each enter. **Reentrant** managers can even be used in a `with` **inside** another `with` of
    the same object, which requires keeping a stack of saved state instead of one attribute: `threading.RLock` is reentrant, `threading.Lock`
    is not (it would deadlock). A manager that stores its saved state in a single attribute silently breaks when nested (problem 10)."""),
    ex("""
    class Indent:
        \"\"\"Reentrant: nested blocks increase the indent, exits restore it.\"\"\"

        def __init__(self):
            self.level = 0
            self._saved = []

        def __enter__(self):
            self._saved.append(self.level)
            self.level += 2
            return self

        def __exit__(self, *exc):
            self.level = self._saved.pop()
            return False

        def line(self, text):
            return " " * self.level + text

    ind = Indent()
    out = [ind.line("start")]
    with ind:
        out.append(ind.line("retrieve"))
        with ind:
            out.append(ind.line("rerank"))
        out.append(ind.line("generate"))
    out.append(ind.line("done"))
    print(out)
    """, "reentrant.py"),
    p("""The standard library is full of context managers worth knowing: `open`, `threading.Lock` and `RLock`, `tempfile.TemporaryDirectory`,
    `decimal.localcontext`, `warnings.catch_warnings` (7.3), `contextlib.suppress` and `redirect_stdout`, `unittest.mock.patch` (13.3), and
    in async code `async with` for HTTP sessions and locks (14.4). LLM SDKs make clients and streaming responses context managers, so
    connections are released even when a loop is abandoned midway."""),
)

section("warmup", "Warm-up",
    predict("Enter, exit and suppression", "easy",
        code="""
        class Gate:
            def __init__(self, name, swallow=()):
                self.name, self.swallow = name, swallow
            def __enter__(self):
                print("open", self.name)
                return self.name.upper()
            def __exit__(self, exc_type, exc, tb):
                print("close", self.name, exc_type.__name__ if exc_type else "-")
                return exc_type is not None and issubclass(exc_type, self.swallow)

        with Gate("a") as g:
            print("using", g)
        with Gate("b", swallow=(KeyError,)):
            {}["missing"]
        print("after b")
        try:
            with Gate("c", swallow=(KeyError,)):
                int("x")
        except ValueError:
            print("ValueError reached the caller")
        """,
        hints=["`as` receives what `__enter__` returns. `__exit__` returning true swallows the exception; here only the listed types."],
        why="""The first block binds the upper-cased name and exits normally. In the second, the `KeyError` is in the swallow list, so `__exit__` returns `True`,
        the exception disappears and execution continues with "after b". In the third, `__exit__` still runs (printing `ValueError`), but returns
        `False` for a type it does not swallow, so the error propagates after the cleanup, which is the behaviour you want almost always."""),
    write("A timer that also times failures", "easy", tag="GenAI",
        prompt="""Write a context manager class `Timer(clock, sink=None)` whose `__enter__` returns the timer, and whose `__exit__` stores the duration in
        `self.elapsed`, sets `self.failed` to whether an exception occurred, appends `(elapsed, failed)` to the list `sink` if given, and never
        suppresses exceptions. The same instance must be reusable in later `with` blocks.""",
        code="""
        class Timer:
            pass
        """,
        tests="""
        ticks = iter([0.0, 0.5, 10.0, 12.0, 20.0, 20.25])
        sink = []
        t = Timer(lambda: next(ticks), sink)
        with t as same:
            pass
        assert same is t and t.elapsed == 0.5 and t.failed is False
        try:
            with t:
                raise TimeoutError("slow model")
            assert False
        except TimeoutError:
            pass
        assert t.elapsed == 2.0 and t.failed is True
        with t:
            pass
        assert sink == [(0.5, False), (2.0, True), (0.25, False)] and t.failed is False
        """,
        hints=["Record `self.start` in `__enter__`; in `__exit__`, `failed = exc_type is not None`; return `False`."],
        solution="""
        class Timer:
            def __init__(self, clock, sink=None):
                self.clock = clock
                self.sink = sink
                self.elapsed = None
                self.failed = None

            def __enter__(self):
                self.start = self.clock()
                return self

            def __exit__(self, exc_type, exc, tb):
                self.elapsed = self.clock() - self.start
                self.failed = exc_type is not None
                if self.sink is not None:
                    self.sink.append((self.elapsed, self.failed))
                return False
        """,
        why="""All the measuring happens in `__exit__`, which runs on success and on failure alike, so slow timeouts are recorded rather than vanishing from
        the statistics. `exc_type is not None` is the standard test for "the block raised". Returning `False` lets the exception continue to the
        caller after it has been timed. Because every `__enter__` records a fresh start, the same timer can be reused for consecutive blocks
        (but not nested, since there is only one `start`). The injected clock makes all of it testable to the exact value."""),
    fix("A manager that hides every error", "easy", tag="Data work",
        prompt="""`ignore_missing` was meant to ignore only `FileNotFoundError` when deleting temporary files. It returns `True` from `__exit__`, so it also
        hides a `PermissionError` and any bug inside the block. Fix it to suppress only `FileNotFoundError`.""",
        code="""
        class ignore_missing:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.suppressed = exc_type
                return True
        """,
        tests="""
        with ignore_missing() as m:
            raise FileNotFoundError("tmp.txt")
        assert m.suppressed is FileNotFoundError
        for err in (PermissionError("in use"), NameError("typo")):
            try:
                with ignore_missing():
                    raise err
                assert False, "must propagate"
            except type(err):
                pass
        with ignore_missing() as m:
            pass
        assert m.suppressed is None
        """,
        hints=["Return `True` only when `exc_type` is not `None` and is `FileNotFoundError` or a subclass of it."],
        solution="""
        class ignore_missing:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.suppressed = exc_type
                return exc_type is not None and issubclass(exc_type, FileNotFoundError)
        """,
        why="""A context manager that returns `True` unconditionally is a bare `except: pass` in disguise (7.3): the `PermissionError` (a real problem) and the
        `NameError` (a bug) vanished just like the harmless missing file. Checking the type with `issubclass` suppresses only what the manager is
        named for. The standard library already provides exactly this, `contextlib.suppress(FileNotFoundError)`, which is usually the better
        choice than writing your own."""),
    predict("A generator manager without finally", "easy",
        code="""
        from contextlib import contextmanager

        @contextmanager
        def fragile(name):
            print("acquire", name)
            yield name
            print("release", name)

        @contextmanager
        def safe(name):
            print("acquire", name)
            try:
                yield name
            finally:
                print("release", name)

        with fragile("a"):
            print("work a")
        for manager in (fragile, safe):
            try:
                with manager("b"):
                    raise ValueError("boom")
            except ValueError:
                print("caller saw the error")
        """,
        hints=["An exception in the body is re-raised at the `yield`. Code after the `yield` runs only if nothing is raised there."],
        why="""Without an error, the code after `yield` runs, so `fragile` releases `a`. When the body raises, the exception is thrown into the generator at the
        `yield`; `fragile` has no `finally`, so its release line is skipped and the resource leaks, while the error still reaches the caller.
        `safe` puts the release in `finally`, so it runs before the error propagates. With `@contextmanager`, `try`/`finally` around the `yield` is
        not optional."""),
)

section("medium", "Medium",
    write("Temporary settings for one request", "medium", tag="GenAI",
        prompt="""Write a `contextlib.contextmanager` function `overrides(obj, **changes)` that sets attributes on `obj` for the duration of the block and
        restores them afterwards, even if the block raises. Attributes that did not exist before must be **deleted** afterwards, not set to
        `None`. If any name in `changes` starts with `_`, raise `ValueError` before changing anything. Yield `obj`.""",
        code="""
        from contextlib import contextmanager

        @contextmanager
        def overrides(obj, **changes):
            pass
        """,
        tests="""
        class Client:
            def __init__(self):
                self.model = "small"
                self.temperature = 0.2

        c = Client()
        with overrides(c, temperature=0.9, seed=7) as same:
            assert same is c and (c.temperature, c.seed, c.model) == (0.9, 7, "small")
        assert c.temperature == 0.2 and not hasattr(c, "seed")
        try:
            with overrides(c, model="large"):
                raise TimeoutError("slow")
        except TimeoutError:
            pass
        assert c.model == "small"
        try:
            with overrides(c, _secret=1, model="x"):
                pass
            assert False
        except ValueError:
            assert c.model == "small" and not hasattr(c, "_secret")
        """,
        hints=["Validate first. Save `{name: getattr(obj, name)}` only for names that exist (`hasattr`), and remember the new ones.",
               "In `finally`, restore saved values and `delattr` the names that were new."],
        solution="""
        from contextlib import contextmanager

        _MISSING = object()

        @contextmanager
        def overrides(obj, **changes):
            private = [k for k in changes if k.startswith("_")]
            if private:
                raise ValueError(f"refusing to override private attributes: {private}")
            saved = {k: getattr(obj, k, _MISSING) for k in changes}
            for k, v in changes.items():
                setattr(obj, k, v)
            try:
                yield obj
            finally:
                for k, old in saved.items():
                    if old is _MISSING:
                        delattr(obj, k)
                    else:
                        setattr(obj, k, old)
        """,
        why="""Saving the old values before changing anything and restoring them in `finally` guarantees the object returns to its exact previous state,
        whether the request succeeds or times out, so a per-request override cannot leak into later requests (9.1's shared-state problem in
        another form). A sentinel distinguishes "the attribute did not exist" from "it existed and was `None`" (2.1), so new attributes are
        removed rather than left behind as `None`. Validation happens before the `yield` and before any change, so a rejected call leaves
        the object untouched. `unittest.mock.patch.object` (13.3) is the industrial version of this manager, used in tests to replace attributes
        temporarily."""),
    fix("A lock that stays locked after an error", "medium", tag="Data work",
        prompt="""`hold(lock)` acquires a lock-like object for the block. When the block raises, the lock is never released, and every later caller
        blocks. Fix the context manager.""",
        code="""
        from contextlib import contextmanager

        @contextmanager
        def hold(lock):
            lock.acquire()
            yield lock
            lock.release()
        """,
        tests="""
        class FakeLock:
            def __init__(self):
                self.held = False
                self.events = []
            def acquire(self):
                assert not self.held, "deadlock: already held"
                self.held = True
                self.events.append("acquire")
            def release(self):
                self.held = False
                self.events.append("release")

        lock = FakeLock()
        with hold(lock):
            assert lock.held
        assert not lock.held
        try:
            with hold(lock):
                raise ValueError("work failed")
        except ValueError:
            pass
        assert not lock.held and lock.events == ["acquire", "release", "acquire", "release"]
        """,
        hints=["Wrap the `yield` in `try`/`finally` and release in the `finally`."],
        solution="""
        from contextlib import contextmanager

        @contextmanager
        def hold(lock):
            lock.acquire()
            try:
                yield lock
            finally:
                lock.release()
        """,
        why="""With `@contextmanager`, an exception in the `with` body is raised at the `yield`, so the line after it never ran and the lock stayed held: the
        next `acquire` would wait forever in real threaded code (here, the fake raises "deadlock" instead). `finally` makes the release
        unconditional while letting the error propagate. The acquire stays **before** the `try`: if acquiring fails, there is nothing to release.
        Real `threading.Lock` objects are context managers already, so `with lock:` is the idiomatic form."""),
    write("Write a file atomically", "medium", tag="ML",
        prompt="""Write a `contextlib.contextmanager` function `atomic_write(path, encoding="utf-8")` that yields a text file handle to a temporary file in the
        same directory; when the block finishes normally, it closes the file and replaces `path` with it (`os.replace`); if the block raises, it
        closes and deletes the temporary file and lets the exception propagate, leaving any existing `path` untouched (7.3).""",
        code="""
        import os
        from contextlib import contextmanager

        @contextmanager
        def atomic_write(path, encoding="utf-8"):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "metrics.json")
        with atomic_write(p) as f:
            f.write('{"f1": 0.81}')
        assert open(p, encoding="utf-8").read() == '{"f1": 0.81}'
        try:
            with atomic_write(p) as f:
                f.write('{"f1": 0.9')
                raise RuntimeError("crashed while writing")
        except RuntimeError:
            pass
        assert open(p, encoding="utf-8").read() == '{"f1": 0.81}'
        assert sorted(os.listdir(d)) == ["metrics.json"]
        with atomic_write(os.path.join(d, "new.txt")) as f:
            f.write("ok")
        assert sorted(os.listdir(d)) == ["metrics.json", "new.txt"]
        """,
        hints=["`tmp = path + \".tmp\"`; open it before the `try`. Use `try` / `except BaseException:` to clean up and re-raise, and `else` for the replace."],
        solution="""
        import os
        from contextlib import contextmanager

        @contextmanager
        def atomic_write(path, encoding="utf-8"):
            tmp = path + ".tmp"
            f = open(tmp, "w", encoding=encoding)
            try:
                yield f
            except BaseException:
                f.close()
                os.remove(tmp)
                raise
            else:
                f.close()
                os.replace(tmp, path)
        """,
        why="""The context manager turns the atomic-write pattern of 7.3 into one line for every caller: they write normally, and either the complete new file
        appears at `path` or nothing changes. `except BaseException` makes even Ctrl+C clean up the temporary file, and the bare `raise` keeps the
        original error. The replace happens in `else`, so it runs only when the block succeeded, and only after the file is closed (flushing
        everything to disk). Model checkpoints, evaluation results and index files should be written this way, since a crash mid-write would
        otherwise leave a corrupt file that the next run tries to load."""),
    choose("Open once or open per line", "medium",
        prompt="Both write 3,000 log lines to a file. Which is faster?",
        setup="""import os, tempfile
path = os.path.join(tempfile.mkdtemp(), "out.log")
lines = [f"request {i} ok\\n" for i in range(3000)]""",
        options={
            "a": "for line in lines:\n    with open(path, \"a\", encoding=\"utf-8\") as f:\n        f.write(line)",
            "b": "with open(path, \"a\", encoding=\"utf-8\") as f:\n    for line in lines:\n        f.write(line)",
        },
        answer="b",
        hints=["What does every `with open(...)` do at the start and at the end?"],
        why="""Each `with open(...)` asks the operating system to open the file, creates a file object with its buffer and encoder, and at exit flushes and
        closes it. Version A pays that 3,000 times; version B once, writing into a buffer that is flushed in large chunks. Keep the `with`
        around the whole job, not around each small step. The exception is long-running processes appending occasionally (a log written once a
        minute), where opening per write avoids holding the file open; logging handlers make that trade-off for you (12.3)."""),
    trace("Nested managers and an exception", "medium",
        prompt="Fill in `log` after each marked line.",
        code="""
        from contextlib import contextmanager
        log = []

        @contextmanager
        def tag(name):
            log.append(f"+{name}")
            try:
                yield
            except KeyError:
                log.append(f"{name} handled KeyError")
            finally:
                log.append(f"-{name}")

        with tag("outer"), tag("inner"):
            log.append("body")  # row: "inside"
        log.clear()
        with tag("outer"):
            with tag("inner"):
                raise KeyError("k")
        log.append("after")  # row: "KeyError in inner"
        """,
        trace_vars=["log"],
        hints=["The innermost manager sees the exception first. Catching it around the `yield` without re-raising suppresses it."],
        why="""Managers enter left to right and exit in reverse, so `inner` closes before `outer`. When the body raises `KeyError`, it is thrown into the inner
        generator at its `yield`; its `except` handles it without re-raising, which **suppresses** it, so its `finally` runs, the outer manager sees
        a normal exit, and execution continues after the block. Suppressing inside a generator manager is as easy as forgetting `raise`, which is
        why the handler should re-raise unless suppression is the point."""),
    fix("A manager that breaks when nested", "medium", tag="ML",
        prompt="""`no_grad` mimics a framework's "disable gradients" switch: inside the block, `STATE["grad"]` is `False`, and afterwards it is restored to its
        previous value. Nested use leaves gradients disabled after the outer block ends. Make it reentrant: each exit restores exactly the value
        that its own enter replaced.""",
        code="""
        STATE = {"grad": True}

        class no_grad:
            def __enter__(self):
                self.previous = STATE["grad"]
                STATE["grad"] = False
                return self

            def __exit__(self, *exc):
                STATE["grad"] = self.previous
                return False

        guard = no_grad()
        """,
        tests="""
        STATE["grad"] = True
        with guard:
            assert STATE["grad"] is False
            with guard:
                assert STATE["grad"] is False
            assert STATE["grad"] is False
        assert STATE["grad"] is True
        with no_grad():
            pass
        assert STATE["grad"] is True
        """,
        hints=["One `previous` attribute is overwritten by the inner `__enter__`. Keep a stack (a list) of saved values: push in `__enter__`, pop in `__exit__`."],
        solution="""
        STATE = {"grad": True}

        class no_grad:
            def __init__(self):
                self._saved = []

            def __enter__(self):
                self._saved.append(STATE["grad"])
                STATE["grad"] = False
                return self

            def __exit__(self, *exc):
                STATE["grad"] = self._saved.pop()
                return False

        guard = no_grad()
        """,
        why="""The outer `__enter__` saved `True`; the inner one, on the **same** object, overwrote `previous` with `False`; the inner exit restored `False`, and
        the outer exit then restored the overwritten value, also `False`, so gradients stayed off for the rest of the program. A stack of saved
        values gives each enter its own slot, popped by the matching exit in reverse order, which is what makes a manager reentrant. Such
        global-switch managers are common in ML frameworks (`torch.no_grad()`, `torch.inference_mode()`), and nesting them happens naturally when
        one helper that disables gradients calls another."""),
    refactor("Repeated try/finally into a context manager", "medium", tag="GenAI",
        prompt="Replace the repeated `try`/`finally` blocks with one context manager, `span(name)`, used by both functions. Same `EVENTS`. Keep the tests green.",
        code="""
        EVENTS = []

        def retrieve(query):
            EVENTS.append(("start", "retrieve"))
            try:
                if not query:
                    raise ValueError("empty query")
                return [f"doc about {query}"]
            finally:
                EVENTS.append(("end", "retrieve"))

        def generate(query, docs):
            EVENTS.append(("start", "generate"))
            try:
                return f"answer from {len(docs)} docs"
            finally:
                EVENTS.append(("end", "generate"))
        """,
        tests="""
        docs = retrieve("refund")
        assert generate("refund", docs) == "answer from 1 docs"
        try:
            retrieve("")
        except ValueError:
            pass
        assert EVENTS == [("start", "retrieve"), ("end", "retrieve"), ("start", "generate"), ("end", "generate"),
                          ("start", "retrieve"), ("end", "retrieve")]
        """,
        hints=["`@contextmanager def span(name):` appends the start event, then `try: yield` / `finally:` appends the end event."],
        solution="""
        from contextlib import contextmanager

        EVENTS = []

        @contextmanager
        def span(name):
            EVENTS.append(("start", name))
            try:
                yield
            finally:
                EVENTS.append(("end", name))

        def retrieve(query):
            with span("retrieve"):
                if not query:
                    raise ValueError("empty query")
                return [f"doc about {query}"]

        def generate(query, docs):
            with span("generate"):
                return f"answer from {len(docs)} docs"
        """,
        why="""The begin/end pairing now lives in one place, and each function body contains only its work, inside a `with` that reads as "this is the
        retrieve span". A `return` inside the `with` block still triggers the exit, exactly like `finally`. Adding timing or error status to every
        span is now one change. Tracing libraries expose exactly this API: OpenTelemetry's `with tracer.start_as_current_span("retrieve"):`,
        Langfuse and LangSmith's context-manager spans."""),
    predict("What __exit__ receives", "medium",
        code="""
        class Inspect:
            def __exit__(self, exc_type, exc, tb):
                print(" ", exc_type.__name__ if exc_type else None, repr(exc), tb is not None)
                return isinstance(exc, ZeroDivisionError)
            def __enter__(self):
                return 42

        with Inspect() as value:
            print(" value", value)
        with Inspect():
            1 / 0
        print("continued")
        def early():
            with Inspect():
                return "returned"
        print(early())
        """,
        hints=["A normal exit, including `return`, passes three `None`s. A suppressed exception lets execution continue after the block."],
        why="""`as` receives 42 from `__enter__`. A normal exit passes `None` for all three arguments. The division error arrives as its type, the exception object
        and a traceback, and since `__exit__` returns `True` for that type, execution continues after the `with`. A `return` inside the block is a
        normal exit for the manager (it still gets `None`s), and the function returns its value after `__exit__` has run."""),
)

section("hard", "Hard",
    write("Nested tracing spans", "hard", tag="GenAI",
        prompt="""Write a class `Tracer(clock)` with a method `span(name)` returning a context manager (use `contextlib.contextmanager`) that records a dict
        `{"name", "parent", "start", "end", "error"}` in `self.spans` (appended when the span **starts**, so outer spans come first). `parent` is the
        name of the enclosing span (or `None`), tracked with a stack; `error` is the exception's type name or `None`; exceptions propagate. Inside
        the block, the yielded value is the span's dict, so code can add attributes (`s["tokens"] = 120`).""",
        code="""
        from contextlib import contextmanager

        class Tracer:
            pass
        """,
        tests="""
        ticks = iter([0.0, 0.1, 0.5, 0.6, 0.9, 1.4, 2.0, 2.5])
        t = Tracer(lambda: next(ticks))
        with t.span("request"):
            with t.span("retrieve") as s:
                s["docs"] = 3
            try:
                with t.span("generate"):
                    raise TimeoutError("slow")
            except TimeoutError:
                pass
        names = [(s["name"], s["parent"], s["error"]) for s in t.spans]
        assert names == [("request", None, None), ("retrieve", "request", None), ("generate", "request", "TimeoutError")]
        assert [(s["start"], s["end"]) for s in t.spans] == [(0.0, 1.4), (0.1, 0.5), (0.6, 0.9)]
        assert t.spans[1]["docs"] == 3 and t._stack == []
        with t.span("solo"):
            pass
        assert t.spans[-1]["parent"] is None and t.spans[-1]["start"] == 2.0
        """,
        hints=["Keep `self._stack` of open span names. In `span`: build the dict with the parent from the top of the stack, append it, push the name, then `try: yield record`.",
               "Use `except BaseException as e:` to set `error`, then `raise`; in `finally`, set `end` and pop the stack."],
        solution="""
        from contextlib import contextmanager

        class Tracer:
            def __init__(self, clock):
                self.clock = clock
                self.spans = []
                self._stack = []

            @contextmanager
            def span(self, name):
                record = {"name": name, "parent": self._stack[-1] if self._stack else None,
                          "start": self.clock(), "end": None, "error": None}
                self.spans.append(record)
                self._stack.append(name)
                try:
                    yield record
                except BaseException as e:
                    record["error"] = type(e).__name__
                    raise
                finally:
                    record["end"] = self.clock()
                    self._stack.pop()
        """,
        why="""The stack of open span names is what turns flat timing into a **tree**: each new span takes the current top as its parent, and its exit pops
        itself, so nesting in the code becomes nesting in the trace, the structure a tracing UI draws as a waterfall. Recording the error type and
        then re-raising keeps the manager transparent to the program while making failures visible in the trace. `@contextmanager` works on methods
        too: `self` is just the first argument of the generator function. Yielding the record lets the body attach attributes such as token counts
        or the number of documents, as OpenTelemetry's `span.set_attribute` does. In concurrent code the stack would live in a
        `contextvars.ContextVar` so that parallel requests do not share it (14.4)."""),
    fix("Read the code: a transaction manager", "hard", tag="Data work",
        prompt="""`Transaction(store)` should apply a batch of changes to a dict-like `store` atomically: inside the block, writes go to a staging dict
        obtained from `as`; on success they are committed to the store; on any exception the store is left unchanged and the exception propagates.
        The code commits after failures, binds `None` to the `as` name, and swallows exceptions. Read it, find the bugs and fix them.""",
        code="""
        class Transaction:
            def __init__(self, store):
                self.store = store
                self.commits = 0

            def __enter__(self):
                self.staged = {}

            def __exit__(self, exc_type, exc, tb):
                self.store.update(self.staged)
                self.commits += 1
                return True
        """,
        tests="""
        store = {"balance": 100}
        tx = Transaction(store)
        with tx as staged:
            staged["balance"] = 80
            staged["last_order"] = "o-1"
        assert store == {"balance": 80, "last_order": "o-1"} and tx.commits == 1
        try:
            with Transaction(store) as staged:
                staged["balance"] = 0
                raise ValueError("payment declined")
            assert False, "the error must propagate"
        except ValueError:
            pass
        assert store == {"balance": 80, "last_order": "o-1"}
        with Transaction(store) as staged:
            pass
        assert store["balance"] == 80
        """,
        hints=["`__enter__` must return the staging dict.", "Commit only when `exc_type is None`; return `False` so exceptions propagate."],
        solution="""
        class Transaction:
            def __init__(self, store):
                self.store = store
                self.commits = 0

            def __enter__(self):
                self.staged = {}
                return self.staged

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    self.store.update(self.staged)
                    self.commits += 1
                self.staged = {}
                return False
        """,
        why="""Three bugs, each a rule of this lesson. `__enter__` returned nothing, so `as staged` received `None` and the first write raised `TypeError`. `__exit__`
        committed unconditionally, so a declined payment was written to the store anyway, the exact opposite of a transaction. And returning
        `True` swallowed every exception, so the caller believed the declined payment succeeded. The fixed manager commits only on a clean exit,
        discards the staged changes in every case, and returns `False` so failures reach the caller after the rollback. Database libraries
        follow this pattern: `with connection:` in `sqlite3` commits on success and rolls back on an exception; SQLAlchemy's `session.begin()`
        does the same."""),
    write("Capture log records in a block", "hard", tag="Data work",
        prompt="""Write a context manager class `capture_logs(logger, level=logging.INFO)` that, for the duration of the block, attaches a handler to `logger`
        collecting records at or above `level`, temporarily lowers the logger's level if needed so they are emitted, and stops propagation to parent
        loggers. `__enter__` returns a list that fills with `(level_name, message)` tuples. On exit, everything is restored exactly (handler removed,
        level and propagation as before), also when the block raises.""",
        code="""
        import logging

        class capture_logs:
            pass
        """,
        tests="""
        import logging
        log = logging.getLogger("rag.pipeline")
        log.setLevel(logging.WARNING)
        log.propagate = True
        before = list(log.handlers)

        with capture_logs(log) as records:
            log.debug("hidden")
            log.info("retrieved %d docs", 3)
            log.warning("slow reranker")
        assert records == [("INFO", "retrieved 3 docs"), ("WARNING", "slow reranker")]
        assert log.level == logging.WARNING and log.propagate is True and log.handlers == before

        try:
            with capture_logs(log, level=logging.ERROR) as records:
                log.warning("ignored")
                log.error("model failed")
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert records == [("ERROR", "model failed")] and log.handlers == before and log.level == logging.WARNING
        """,
        hints=["A handler subclass with `emit(self, record)` can append `(record.levelname, record.getMessage())` to a list (12.3).",
               "Save `logger.level` and `logger.propagate` in `__enter__`; restore them and `removeHandler` in `__exit__`."],
        solution="""
        import logging

        class _ListHandler(logging.Handler):
            def __init__(self, records, level):
                super().__init__(level)
                self.records = records

            def emit(self, record):
                self.records.append((record.levelname, record.getMessage()))


        class capture_logs:
            def __init__(self, logger, level=logging.INFO):
                self.logger = logger
                self.level = level

            def __enter__(self):
                self.records = []
                self._handler = _ListHandler(self.records, self.level)
                self._old_level = self.logger.level
                self._old_propagate = self.logger.propagate
                self.logger.addHandler(self._handler)
                if self.logger.getEffectiveLevel() > self.level:
                    self.logger.setLevel(self.level)
                self.logger.propagate = False
                return self.records

            def __exit__(self, exc_type, exc, tb):
                self.logger.removeHandler(self._handler)
                self.logger.setLevel(self._old_level)
                self.logger.propagate = self._old_propagate
                return False
        """,
        why="""The manager changes three pieces of global state (the handler list, the level, and propagation) and puts all three back on every exit, so a test
        or a debugging session cannot leave the application's logging configuration altered, even when the block fails. Lowering the logger's
        level matters: a logger set to `WARNING` drops `INFO` records before any handler sees them, so the capture would silently miss them; the
        handler's own level then filters to what was asked for. Stopping propagation keeps captured records out of other handlers during the
        block. `record.getMessage()` applies the `%`-style arguments, which is why the message reads "retrieved 3 docs". pytest's `caplog`
        fixture and `unittest`'s `assertLogs` are built the same way."""),
    predict("Single-use generator managers", "hard",
        code="""
        from contextlib import contextmanager

        @contextmanager
        def once():
            print("  setup")
            yield "value"
            print("  teardown")

        cm = once()
        with cm as v:
            print("  first", v)
        try:
            with cm:
                pass
        except (RuntimeError, AttributeError) as e:
            print("second use failed:", type(e).__name__)

        @contextmanager
        def twice():
            yield 1
            yield 2

        try:
            with twice():
                pass
        except RuntimeError as e:
            print("RuntimeError:", e)

        @contextmanager
        def swallow():
            try:
                yield
            except ValueError:
                print("  swallowed")

        with swallow():
            raise ValueError("x")
        print("after swallow")
        """,
        hints=["A `@contextmanager` object wraps one generator, which can run once, so a second `with` on the same object fails. The generator must yield exactly once."],
        why="""The first `with` runs the generator to its end. Reusing the same object fails: the manager discards its stored function and arguments on
        first use, so Python 3.14 raises `AttributeError` (older versions raised `RuntimeError`, "generator didn't yield"); either way, call
        `once()` again for each `with`. A generator that yields a second time breaks the protocol, since the
        manager expects it to finish after the block, so it raises `RuntimeError` ("generator didn't stop"). In `swallow`, catching the exception
        around the `yield` without re-raising suppresses it, so execution continues after the block, the generator-manager equivalent of returning
        `True` from `__exit__`."""),
)

section("interview", "Interview questions",
    explain("What does the `with` statement do, exactly?", "medium", tag="Interview",
        why="""It evaluates the expression to get a context manager, calls its `__enter__()` and binds the return value to the `as` target, runs the block, and
        then always calls `__exit__(exc_type, exc_value, traceback)`, whether the block finished normally, returned, broke out of a loop, or raised.
        For a normal exit the three arguments are `None`; for an exception they describe it, and if `__exit__` returns a true value the exception
        is suppressed, otherwise it propagates after the cleanup. If `__enter__` raises, the block does not run and `__exit__` is not called. With
        several managers in one statement, they enter left to right and exit in reverse. It is equivalent to a carefully written `try`/`finally`
        (with exception information passed to the cleanup), packaged so that callers cannot forget the cleanup."""),
    explain("When would you write a context manager as a class, and when with `contextlib.contextmanager`?", "medium", tag="Interview",
        why="""`@contextmanager` is best for simple setup/cleanup pairs: a generator function with setup before a single `yield`, the value to bind yielded, and
        cleanup after it inside `finally` (mandatory, because exceptions from the block are re-raised at the `yield`). It is short and readable, but
        each call produces a single-use manager. A class with `__enter__` and `__exit__` fits when the manager has state or behaviour beyond the
        block: it is reused or must be reentrant (keeping a stack of saved state), it exposes results after the block (a timer's elapsed time), it
        is also an ordinary object with methods (a file, a client, a lock), it needs fine-grained exception handling in `__exit__`, or it will be
        subclassed. Either way, suppress exceptions only deliberately and for specific types, and use `contextlib.suppress`, `ExitStack` and
        `nullcontext` from the standard library before writing your own."""),
    explain("How do you make sure resources such as HTTP clients, streaming responses and connection pools are cleaned up in an LLM service?", "hard", tag="Interview",
        why="""Tie every resource to a scope with a context manager. Create long-lived resources (an HTTP client with its connection pool, a database pool, a
        vector store client) once at application start-up and close them at shutdown, using the framework's lifespan hook, which is itself a
        context manager (FastAPI's `lifespan`), rather than creating a client per request, which wastes connections. For per-request resources,
        use `with` (or `async with`): streaming responses from LLM SDKs are context managers that close the underlying connection even if the
        consumer stops reading early, temporary files go through `tempfile` managers, and locks are always taken with `with`. Make sure cleanup
        also runs on cancellation: when a client disconnects, the framework cancels the task, which raises inside your code, and only `finally`
        blocks and context managers still run, so put the release logic there. Use `ExitStack` (10.3) when the number of resources is dynamic,
        set timeouts so a stuck resource cannot block forever, and monitor pool usage to catch leaks early."""),
)

recap(
    "`with mgr as x:` calls `__enter__` (its return value becomes `x`), runs the block, then always calls `__exit__(type, value, tb)`.",
    "`__exit__` returning true suppresses the exception: do it only for specific types; return `False` to propagate after cleanup.",
    "`@contextmanager` turns a one-`yield` generator into a manager; put the cleanup in `finally` around the `yield`, or errors skip it.",
    "Several managers enter left to right and exit in reverse; a `return` inside the block is a normal exit.",
    "Generator managers are single-use; a reusable or reentrant class keeps a stack of saved state for nested use.",
)
