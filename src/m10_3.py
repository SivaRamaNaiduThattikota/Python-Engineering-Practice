from lesson import *

lesson(
    id="m10-3", num="10.3", title="Resource patterns",
    intro="The toolbox for managing resources beyond a single `with`: `contextlib.ExitStack` for a dynamic number of "
          "resources and for undo actions, `suppress`, `nullcontext`, `closing` and `redirect_stdout`, classes that own a "
          "resource and close it reliably, temporary global state, cooperative deadlines, and pools. Why `__del__` is not "
          "cleanup. Applied to files, seeds, clients, workspaces and compensating actions.",
    desc="`ExitStack`, `suppress`, timers, temporary state, closing clients.",
    keys="exitstack enter_context callback pop_all contextlib suppress nullcontext closing redirect_stdout chdir resource owner close idempotent __del__ finalize random seed state deadline pool compensating action saga undo",
)

term("ExitStack", "A context manager that collects other context managers and cleanup callbacks at run time and exits all of them, in reverse order, when the block ends.")
term("Idempotent close", "A `close()` that can safely be called more than once: the second call does nothing.")
term("Compensating action", "An undo step registered after an action succeeds, run if a later step fails, so a multi-step operation leaves no half-done state.")

section("exitstack", "`ExitStack`: a dynamic number of resources",
    p("""A `with` statement names its context managers in the code, so it cannot open "one file per input path" when the number of paths is only
    known at run time. **`contextlib.ExitStack`** solves that: it is a context manager that you fill while the block runs. `stack.enter_context(cm)`
    enters `cm` and remembers to exit it; `stack.callback(func, *args)` registers any cleanup function. When the `with ExitStack()` block ends,
    normally or by an exception, everything registered is exited or called in **reverse** order, exactly as nested `with` statements would.
    If opening the fifth file fails, the four already open are closed."""),
    ex("""
    import os, tempfile
    from contextlib import ExitStack

    d = tempfile.mkdtemp()
    paths = []
    for name, text in [("a.txt", "alpha"), ("b.txt", "beta"), ("c.txt", "gamma")]:
        paths.append(os.path.join(d, name))
        with open(paths[-1], "w", encoding="utf-8") as f:
            f.write(text)

    events = []
    with ExitStack() as stack:
        files = [stack.enter_context(open(p, encoding="utf-8")) for p in paths]
        stack.callback(events.append, "callback ran last-in, first-out")
        print([f.read() for f in files])
    print(all(f.closed for f in files), events)

    try:
        with ExitStack() as stack:
            opened = [stack.enter_context(open(p, encoding="utf-8")) for p in paths + [os.path.join(d, "missing.txt")]]
    except FileNotFoundError:
        print("missing file: the three opened ones were closed:", all(f.closed for f in files))
    """, "exitstack.py"),
    p("""Two more methods make `ExitStack` useful beyond files. **`pop_all()`** moves everything registered so far into a **new** stack and leaves
    the current one empty, so the `with` block ends without closing anything: the pattern for a function that acquires several resources
    safely (if any acquisition fails, the earlier ones are released) and then hands them, still open, to its caller (problem 6). And
    **callbacks** turn any cleanup into part of the stack: deleting a temporary file, restoring a setting, sending an "aborted" event, or
    undoing a step that already happened (problem 15)."""),
)

section("helpers", "Small helpers from `contextlib`",
    p("""The `contextlib` module has a few one-line managers that remove a lot of boilerplate. **`suppress(*exceptions)`** ignores the listed
    exception types inside the block (7.3, 10.2). **`nullcontext(value)`** is a manager that does nothing and yields `value`, for code where a
    manager is optional: `with (lock if lock else nullcontext()):`. **`closing(obj)`** turns any object with a `close()` method into a
    manager that calls `close()` at the end, for older libraries that never implemented `__enter__`. **`redirect_stdout(target)`** (and
    `redirect_stderr`) sends `print` output to a file-like object for the duration of the block, which is how you capture the output of code
    that prints instead of returning. **`chdir(path)`** (Python 3.11+) changes the working directory temporarily."""),
    ex("""
    import io
    from contextlib import suppress, nullcontext, closing, redirect_stdout

    class LegacyConnection:
        def __init__(self):
            self.open = True
        def close(self):
            self.open = False

    with closing(LegacyConnection()) as conn:
        print("open inside:", conn.open)
    print("open after:", conn.open)

    def process(items, lock=None):
        with lock if lock is not None else nullcontext():
            return sum(items)
    print(process([1, 2, 3]))

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("this goes into the buffer")
        help_text = "captured"
    print(repr(buf.getvalue()), help_text)

    cache = {"a": 1}
    with suppress(KeyError):
        del cache["missing"]
    print(cache)
    """, "contextlib_helpers.py"),
)

section("owners", "Classes that own a resource",
    p("""An object that holds a connection, a session, a file or a subprocess **owns** that resource and should offer three things. A `close()`
    method that releases it and is **idempotent** (calling it twice is harmless, since cleanup code often runs from several places). Context
    manager support, `__enter__` returning `self` and `__exit__` calling `close()`, so `with Client() as c:` works. And a clear error when the
    object is used after closing, instead of a confusing failure deep inside the library (problem 7). This is the interface of files,
    `sqlite3` connections, `httpx.Client`, and the OpenAI and Anthropic SDK clients."""),
    p("""What not to rely on is **`__del__`**, the finaliser Python may call when an object is garbage-collected. It runs at an unpredictable time
    (or, at interpreter shutdown, possibly not at all), it runs when other objects it needs may already be gone, exceptions inside it are
    ignored with only a warning, and reference cycles can delay it indefinitely (2.1). Use `with` or explicit `close()` for cleanup; if you
    need a last-resort safety net, `weakref.finalize(obj, cleanup_func)` is more predictable than `__del__`."""),
    ex("""
    class Session:
        def __init__(self, name):
            self.name = name
            self._closed = False
            self.requests = 0

        @property
        def closed(self):
            return self._closed

        def send(self, payload):
            if self._closed:
                raise RuntimeError(f"session {self.name} is closed")
            self.requests += 1
            return f"sent {payload}"

        def close(self):
            if not self._closed:          # idempotent
                self._closed = True
                print(f"  {self.name}: released after {self.requests} requests")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.close()
            return False

    with Session("api") as s:
        s.send("a"); s.send("b")
    s.close()                             # harmless second close
    try:
        s.send("c")
    except RuntimeError as e:
        print("RuntimeError:", e)
    """, "resource_owner.py"),
)

section("state", "Temporary global state",
    p("""Some state is global to the process: the random number generator's state, environment variables, the current working directory, logging
    levels, NumPy's print options, a framework's "gradients enabled" switch (10.2). Code that changes it for a moment must **save and restore**
    the exact previous value, not reset it to some default, or it silently changes behaviour for everything that runs afterwards. A context
    manager is the right shape: save in `__enter__` (or before `yield`), restore in `__exit__` (or `finally`). For randomness, that means
    `random.getstate()` and `random.setstate()`, not `random.seed(0)` on exit (problem 9)."""),
    ex("""
    import os, random
    from contextlib import contextmanager

    @contextmanager
    def seeded(seed):
        state = random.getstate()
        random.seed(seed)
        try:
            yield
        finally:
            random.setstate(state)

    @contextmanager
    def env(**values):
        old = {k: os.environ.get(k) for k in values}
        os.environ.update(values)
        try:
            yield
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    random.seed(123)
    before = random.random()
    random.seed(123)
    with seeded(7):
        sample = [random.randint(1, 6) for _ in range(5)]
    after = random.random()
    print(sample, after == before)

    with env(LLM_MODEL="large"):
        print("inside:", os.environ["LLM_MODEL"])
    print("after:", os.environ.get("LLM_MODEL"))
    """, "global_state.py"),
    p("""`after == before` shows that the code outside the block got exactly the random numbers it would have got without the block: the seeded
    section was invisible to it. That property is what keeps experiments reproducible when a library seeds randomness internally. Better
    still, avoid global state where you can: pass a `random.Random(seed)` instance (7.4) or a NumPy `Generator` to the code that needs
    randomness."""),
)

section("deadline", "Timers, deadlines and budgets as scopes",
    p("""A context manager is a natural way to give a block of work a **budget**: a time limit, a token budget, a maximum number of model calls.
    In synchronous Python a manager cannot interrupt the block (8.3), so these scopes are **cooperative**: the block checks the budget at safe
    points (`deadline.check()` before each retry or each document), and the manager records whether the budget was exceeded when the block
    ends. With asyncio, `asyncio.timeout(seconds)` (14.5) can cancel the waiting task, which is the main reason timeouts work better in async
    code."""),
    ex("""
    import time
    from contextlib import contextmanager

    class Deadline:
        def __init__(self, seconds, clock):
            self.seconds, self.clock = seconds, clock
            self.start = clock()

        def remaining(self):
            return self.seconds - (self.clock() - self.start)

        def check(self, step=""):
            if self.remaining() <= 0:
                raise TimeoutError(f"deadline of {self.seconds}s exceeded at {step or 'check'}")

    @contextmanager
    def deadline(seconds, clock=time.monotonic):
        d = Deadline(seconds, clock)
        yield d

    ticks = iter([0.0, 1.0, 2.5, 3.5, 6.0])
    done = []
    try:
        with deadline(5, clock=lambda: next(ticks)) as d:
            for doc in ["a", "b", "c", "d"]:
                d.check(f"doc {doc}")
                done.append(doc)
    except TimeoutError as e:
        print(done, "|", e)
    """, "deadline.py"),
    p("""Each `check` reads the clock once, so the scripted times make the outcome exact: three documents fit, and the fourth check finds the five
    seconds used up. Passing `d.remaining()` as the timeout of each network call is the other half of a deadline (7.4): no single call can then
    run past the budget either (problem 11)."""),
)

section("pools", "Pools: borrowing and returning resources",
    p("""Some resources are expensive to create and limited in number: database connections, browser instances, GPU workers, licensed API sessions.
    A **pool** creates a few, lends one out per task, and takes it back afterwards, so tasks do not pay the creation cost and the total stays
    bounded. Lending is a context manager: `with pool.acquire() as conn:` returns the connection to the pool when the block ends, even if it
    raised. A subtle rule: if the block failed **because the resource is broken** (the connection dropped), the pool must discard that
    resource rather than lend it to the next task (problem 13). Connection pools in `psycopg`, SQLAlchemy and `httpx` follow this design."""),
)

section("warmup", "Warm-up",
    predict("Exit order on a stack", "easy",
        code="""
        from contextlib import ExitStack, contextmanager

        log = []

        @contextmanager
        def res(name):
            log.append(f"open {name}")
            try:
                yield name
            finally:
                log.append(f"close {name}")

        with ExitStack() as stack:
            for name in ["db", "cache", "queue"]:
                stack.enter_context(res(name))
            stack.callback(log.append, "flush metrics")
            log.append("work")
        print(log)
        """,
        hints=["Everything registered on the stack is unwound in reverse order of registration, callbacks included."],
        why="""The three resources are opened in loop order, then the callback is registered last. At the end of the block the stack unwinds last-in,
        first-out: the callback runs first, then `queue`, `cache` and `db` are closed in reverse order of opening, exactly like three nested
        `with` statements with a `finally` inside the innermost."""),
    write("Reproducible randomness in a block", "easy", tag="ML",
        prompt="""Write a `contextlib.contextmanager` function `seeded(seed)` that seeds Python's global `random` module for the duration of the block and,
        afterwards, restores the generator to **exactly** the state it had before, so code outside the block is unaffected. Yield nothing.""",
        code="""
        import random
        from contextlib import contextmanager

        @contextmanager
        def seeded(seed):
            pass
        """,
        tests="""
        import random
        with seeded(42):
            first = [random.random() for _ in range(3)]
        with seeded(42):
            second = [random.random() for _ in range(3)]
        assert first == second

        random.seed(99)
        expected = [random.random() for _ in range(2)]
        random.seed(99)
        a = random.random()
        with seeded(1):
            random.random()
        b = random.random()
        assert [a, b] == expected
        try:
            with seeded(5):
                raise ValueError("x")
        except ValueError:
            pass
        random.seed(3); x = random.random(); random.seed(3)
        with seeded(8):
            pass
        assert random.random() == x
        """,
        hints=["`state = random.getstate()` before seeding; `random.setstate(state)` in a `finally` after the `yield`."],
        solution="""
        import random
        from contextlib import contextmanager

        @contextmanager
        def seeded(seed):
            state = random.getstate()
            random.seed(seed)
            try:
                yield
            finally:
                random.setstate(state)
        """,
        why="""Inside the block the sequence is fixed by the seed, so two seeded blocks give identical numbers, the property you want for a deterministic data
        shuffle or sample. Outside, `getstate`/`setstate` put the generator back exactly where it was, so the surrounding code receives the same
        numbers as if the block had never run (the second test). Resetting to a fixed seed on exit instead would make every later random number in
        the program depend on this block. `finally` restores the state even when the block raises."""),
    fix("An object with close() but no with support", "easy", tag="Data work",
        prompt="""`Exporter` has `close()` but no context manager methods, so `with Exporter(...) as e:` fails with `TypeError ... does not support the context
        manager protocol`. Add context manager support so it closes on exit (also after errors) and returns itself from `__enter__`.""",
        code="""
        class Exporter:
            def __init__(self, sink):
                self.sink = sink
                self.closed = False

            def write(self, row):
                if self.closed:
                    raise RuntimeError("exporter is closed")
                self.sink.append(row)

            def close(self):
                self.closed = True
        """,
        tests="""
        sink = []
        with Exporter(sink) as e:
            e.write({"id": 1})
        assert e.closed and sink == [{"id": 1}]
        try:
            with Exporter(sink) as e2:
                e2.write({"id": 2})
                raise ValueError("bad row")
        except ValueError:
            pass
        assert e2.closed and sink == [{"id": 1}, {"id": 2}]
        try:
            e2.write({"id": 3})
            assert False
        except RuntimeError:
            pass
        """,
        hints=["`__enter__` returns `self`; `__exit__(self, exc_type, exc, tb)` calls `self.close()` and returns `False`."],
        solution="""
        class Exporter:
            def __init__(self, sink):
                self.sink = sink
                self.closed = False

            def write(self, row):
                if self.closed:
                    raise RuntimeError("exporter is closed")
                self.sink.append(row)

            def close(self):
                self.closed = True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.close()
                return False
        """,
        why="""`with` requires `__enter__` and `__exit__`; an object that only has `close()` does not qualify, which is why `contextlib.closing(obj)` exists for
        third-party objects you cannot change. For your own classes, adding the two methods is better: every user gets `with Exporter(...) as
        e:` and the cleanup is guaranteed even when a row fails. Returning `False` from `__exit__` lets the `ValueError` reach the caller after
        the exporter has closed. The closed check in `write` turns use-after-close into a clear error."""),
    predict("nullcontext, suppress and redirect_stdout", "easy",
        code="""
        import io
        from contextlib import nullcontext, suppress, redirect_stdout

        with nullcontext("value") as v:
            print("got", v)

        with suppress(ZeroDivisionError, KeyError):
            print("before")
            1 / 0
            print("never")
        print("after")

        buf = io.StringIO()
        with redirect_stdout(buf):
            print("hidden line")
            print("another")
        print(buf.getvalue().splitlines(), len(buf.getvalue()))
        """,
        hints=["`suppress` ends the block at the first suppressed exception. `redirect_stdout` sends `print` output to the buffer."],
        why="""`nullcontext` simply yields its argument and does nothing else. `suppress` behaves like `try`/`except ...: pass` around the block, so the division
        error ends the block without reaching "never", and execution continues after it. While stdout is redirected, `print` writes into the buffer
        (two lines, each with its newline, 12 + 8 = 20 characters), and printing returns to the console afterwards."""),
)

section("medium", "Medium",
    write("Open a variable number of files", "medium", tag="Data work",
        prompt="""Write a `contextlib.contextmanager` function `open_all(paths, encoding="utf-8")` that opens every path for reading and yields the list of file
        objects in the same order. All files must be closed when the block ends, also on error; if opening any file fails, the files already opened
        must be closed before the error propagates. Use `ExitStack`.""",
        code="""
        from contextlib import ExitStack, contextmanager

        @contextmanager
        def open_all(paths, encoding="utf-8"):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        paths = []
        for i, text in enumerate(["refund policy", "reset password", "invoice copy"]):
            paths.append(os.path.join(d, f"doc{i}.txt"))
            with open(paths[-1], "w", encoding="utf-8") as f:
                f.write(text)

        with open_all(paths) as files:
            contents = [f.read() for f in files]
        assert contents == ["refund policy", "reset password", "invoice copy"]
        assert all(f.closed for f in files)

        try:
            with open_all(paths[:2] + [os.path.join(d, "nope.txt")]) as files:
                pass
            assert False
        except FileNotFoundError:
            pass
        with open_all([]) as none:
            pass
        assert none == []
        """,
        hints=["`with ExitStack() as stack:` then `files = [stack.enter_context(open(p, encoding=encoding)) for p in paths]`, then `yield files`."],
        solution="""
        from contextlib import ExitStack, contextmanager

        @contextmanager
        def open_all(paths, encoding="utf-8"):
            with ExitStack() as stack:
                files = [stack.enter_context(open(p, encoding=encoding)) for p in paths]
                yield files
        """,
        why="""The stack registers each file the moment it is opened, so if the third `open` raises, the stack's own exit closes the first two before the
        `FileNotFoundError` propagates: there is no window in which an opened file is not owned by something. Yielding inside the `with
        ExitStack()` keeps all files open exactly for the caller's block, and the caller's exceptions pass through the stack too. Writing this with
        nested `with` statements is impossible for a variable number of paths, and writing it with `try`/`finally` correctly is surprisingly hard;
        this is the canonical `ExitStack` use."""),
    fix("Resources closed before the caller can use them", "medium", tag="GenAI",
        prompt="""`connect_all(factories)` should create one connection per factory, closing the ones already created if any factory fails, and return the list of
        **open** connections together with a stack the caller uses to close them later. It returns connections that are already closed. Fix it with
        `ExitStack.pop_all()`.""",
        code="""
        from contextlib import ExitStack

        def connect_all(factories):
            with ExitStack() as stack:
                conns = [stack.enter_context(f()) for f in factories]
                return conns, stack
        """,
        tests="""
        class Conn:
            log = []
            def __init__(self, name, fail=False):
                if fail:
                    raise ConnectionError(name)
                self.name, self.open = name, True
                Conn.log.append(f"open {name}")
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                self.open = False
                Conn.log.append(f"close {self.name}")
                return False

        conns, stack = connect_all([lambda: Conn("db"), lambda: Conn("cache")])
        assert all(c.open for c in conns)
        with stack:
            pass
        assert not any(c.open for c in conns)
        Conn.log.clear()
        try:
            connect_all([lambda: Conn("db"), lambda: Conn("bad", fail=True)])
            assert False
        except ConnectionError:
            assert Conn.log == ["open db", "close db"]
        """,
        hints=["`return conns, stack.pop_all()`: the new stack owns the connections, and the `with` block ends with nothing left to close."],
        solution="""
        from contextlib import ExitStack

        def connect_all(factories):
            with ExitStack() as stack:
                conns = [stack.enter_context(f()) for f in factories]
                return conns, stack.pop_all()
        """,
        why="""`return` inside a `with` block still exits it, so the stack closed every connection on the way out, and the caller received closed objects. The
        `with ExitStack()` is still the right structure for the **acquisition**: if the second factory fails, the first connection is closed (the
        last test). `pop_all()` transfers ownership of everything registered so far into a fresh stack and empties the current one, so the normal
        exit closes nothing, and the caller holds a stack that will close all connections when it is exited. This "acquire safely, then hand over"
        pattern is how connection setup in application start-up code is written."""),
    write("A client that owns its session", "medium", tag="GenAI",
        prompt="""Write a class `LLMClient(make_session)` where `make_session()` returns a session object with `post(payload)` and `close()`. The client creates
        its session **lazily** on the first request; `complete(prompt)` posts `{"prompt": prompt}` and returns the result; `close()` closes the
        session (if one was created) and is idempotent; `closed` is a read-only property; using a closed client raises `RuntimeError("client is
        closed")`. Support `with`.""",
        code="""
        class LLMClient:
            pass
        """,
        tests="""
        made = []
        class FakeSession:
            def __init__(self):
                self.closes = 0
                made.append(self)
            def post(self, payload):
                return f"answer to {payload['prompt']}"
            def close(self):
                self.closes += 1

        with LLMClient(FakeSession) as client:
            assert made == []
            assert client.complete("refund?") == "answer to refund?" and client.complete("x") == "answer to x"
        assert len(made) == 1 and made[0].closes == 1 and client.closed
        client.close()
        assert made[0].closes == 1
        try:
            client.complete("again")
            assert False
        except RuntimeError as e:
            assert str(e) == "client is closed"
        unused = LLMClient(FakeSession)
        unused.close()
        assert len(made) == 1 and unused.closed
        try:
            unused.closed = False
            assert False
        except AttributeError:
            pass
        """,
        hints=["Keep `self._session = None` and `self._closed = False`; a private `_get_session()` creates the session on first use."],
        solution="""
        class LLMClient:
            def __init__(self, make_session):
                self._make_session = make_session
                self._session = None
                self._closed = False

            @property
            def closed(self):
                return self._closed

            def _get_session(self):
                if self._closed:
                    raise RuntimeError("client is closed")
                if self._session is None:
                    self._session = self._make_session()
                return self._session

            def complete(self, prompt):
                return self._get_session().post({"prompt": prompt})

            def close(self):
                if self._closed:
                    return
                self._closed = True
                if self._session is not None:
                    self._session.close()
                    self._session = None

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.close()
                return False
        """,
        why="""The client is the single owner of the session: it creates it (lazily, so a client that is never used opens no connection), reuses it for every
        request (one connection pool, not one per call), and closes it exactly once, however many times `close()` is called and whether the `with`
        block succeeded or not. The closed state is read-only from outside (9.3), and use-after-close fails with a message that says what happened.
        Taking `make_session` as a parameter is dependency injection (9.5), so tests pass a fake session. Real SDK clients (`OpenAI()`,
        `anthropic.Anthropic()`, `httpx.Client()`) behave this way, which is why you should create one client per application and close it at
        shutdown rather than one per request."""),
    trace("Callbacks and an exception on the stack", "medium",
        prompt="Fill in `log` after each marked line.",
        code="""
        from contextlib import ExitStack
        log = []

        with ExitStack() as stack:
            stack.callback(log.append, "undo step 1")
            stack.callback(log.append, "undo step 2")
            log.append("work")  # row: "inside the block"

        log.clear()
        try:
            with ExitStack() as stack:
                stack.callback(log.append, "release a")
                log.append("step a")
                raise ValueError("step b failed")
        except ValueError:
            log.append("caller")  # row: "after a failure"

        log.clear()
        with ExitStack() as stack:
            stack.callback(log.append, "should not run")
            moved = stack.pop_all()
            log.append("popped")
        moved.close()
        log.append("end")  # row: "after pop_all and close"
        """,
        trace_vars=["log"],
        hints=["Callbacks run at the end of the block, last registered first. `pop_all` moves them to a new stack; `close()` runs them."],
        why="""Inside the block nothing has been undone yet; the callbacks run at the exit, in reverse order (not shown in the first row). On failure, the callback
        still runs, before the caller's handler, like a `finally`. After `pop_all`, the original stack is empty, so its exit runs nothing, and the
        callback runs only when the new stack is closed explicitly."""),
    fix("A seed scope that changes global randomness", "medium", tag="ML",
        prompt="""`fixed_seed(seed)` should make a block reproducible without affecting the rest of the program, but it calls `random.seed(0)` on exit, so every
        random number after the block is the same on every run and different from what it would have been. Fix it to restore the previous state.""",
        code="""
        import random
        from contextlib import contextmanager

        @contextmanager
        def fixed_seed(seed):
            random.seed(seed)
            try:
                yield
            finally:
                random.seed(0)
        """,
        tests="""
        import random
        random.seed(2024)
        reference = [random.random() for _ in range(3)]
        random.seed(2024)
        got = [random.random()]
        with fixed_seed(11):
            inside = random.random()
        got += [random.random(), random.random()]
        assert got == reference
        with fixed_seed(11):
            again = random.random()
        assert again == inside
        """,
        hints=["Save `random.getstate()` before seeding and restore it with `random.setstate` in the `finally`."],
        solution="""
        import random
        from contextlib import contextmanager

        @contextmanager
        def fixed_seed(seed):
            state = random.getstate()
            random.seed(seed)
            try:
                yield
            finally:
                random.setstate(state)
        """,
        why="""Seeding to a fixed value on exit is not "restoring": it replaces whatever state the program had with a new one, so every random choice after the
        block (data shuffling, dropout, sampling) changes, and a later experiment can no longer be reproduced from its own seed. Saving the full
        generator state and putting it back makes the block invisible from outside, which the test checks by comparing against a run without the
        block. The general rule for temporary global state: save the exact old value, restore that value, in `finally`."""),
    refactor("Nested conditional withs into an ExitStack", "medium", tag="Data work",
        prompt="Replace the nested, duplicated `with` blocks by one `ExitStack`, same behaviour. Keep the tests green.",
        code="""
        from contextlib import contextmanager

        LOG = []

        @contextmanager
        def resource(name):
            LOG.append(f"open {name}")
            try:
                yield name
            finally:
                LOG.append(f"close {name}")

        def run(job, use_cache, use_lock):
            if use_cache and use_lock:
                with resource("cache"):
                    with resource("lock"):
                        return f"{job} with cache+lock"
            elif use_cache:
                with resource("cache"):
                    return f"{job} with cache"
            elif use_lock:
                with resource("lock"):
                    return f"{job} with lock"
            return f"{job} plain"
        """,
        tests="""
        assert run("a", True, True) == "a with cache+lock"
        assert LOG == ["open cache", "open lock", "close lock", "close cache"]
        LOG.clear()
        assert run("b", False, True) == "b with lock" and LOG == ["open lock", "close lock"]
        LOG.clear()
        assert run("c", False, False) == "c plain" and LOG == []
        LOG.clear()
        assert run("d", True, False) == "d with cache" and LOG == ["open cache", "close cache"]
        """,
        hints=["Enter each optional resource with `stack.enter_context(...)` inside an `if`, collect their names, then build the result once."],
        solution="""
        from contextlib import ExitStack, contextmanager

        LOG = []

        @contextmanager
        def resource(name):
            LOG.append(f"open {name}")
            try:
                yield name
            finally:
                LOG.append(f"close {name}")

        def run(job, use_cache, use_lock):
            with ExitStack() as stack:
                used = []
                if use_cache:
                    used.append(stack.enter_context(resource("cache")))
                if use_lock:
                    used.append(stack.enter_context(resource("lock")))
                return f"{job} with {'+'.join(used)}" if used else f"{job} plain"
        """,
        why="""Every combination of optional resources needed its own branch, so two options already meant four branches, and three would mean eight. With an
        `ExitStack`, each resource is an independent `if` that registers it, the order of opening (and therefore of closing) stays the same, and
        the work is written once. This is the general cure for "optional context managers" when there are several; for a single optional one,
        `nullcontext` is enough."""),
    write("A cooperative deadline", "medium", tag="GenAI",
        prompt="""Write a class `Deadline(seconds, clock)` usable as a context manager. Inside the block, `remaining()` returns the seconds left (never below 0),
        `check(step)` raises `TimeoutError(f"deadline exceeded at {step}")` when no time is left, and `timeout_for(default)` returns
        `min(default, remaining())` for passing to network calls. On exit, record `self.elapsed` and `self.overrun` (true if the block ended after the
        deadline). The clock starts at `__enter__`, so the object can be created early and entered later; exceptions propagate.""",
        code="""
        class Deadline:
            pass
        """,
        tests="""
        ticks = iter([100.0, 101.0, 102.0, 104.5, 106.0, 106.0])
        done = []
        try:
            with Deadline(5, lambda: next(ticks)) as d:
                for step in ["retrieve", "rerank", "generate", "verify"]:
                    d.check(step)
                    done.append(step)
            assert False
        except TimeoutError as e:
            assert str(e) == "deadline exceeded at verify" and done == ["retrieve", "rerank", "generate"]
        assert d.elapsed == 6.0 and d.overrun is True

        ticks2 = iter([0.0, 1.0, 1.0, 2.0])
        with Deadline(10, lambda: next(ticks2)) as d2:
            assert d2.remaining() == 9.0 and d2.timeout_for(30) == 9.0
        assert d2.elapsed == 2.0 and d2.overrun is False
        """,
        hints=["Set `self.start = self.clock()` in `__enter__`. `remaining()` is `max(0.0, seconds - (clock() - start))`."],
        solution="""
        class Deadline:
            def __init__(self, seconds, clock):
                self.seconds = seconds
                self.clock = clock
                self.elapsed = None
                self.overrun = None

            def __enter__(self):
                self.start = self.clock()
                return self

            def remaining(self):
                return max(0.0, self.seconds - (self.clock() - self.start))

            def check(self, step):
                if self.remaining() <= 0:
                    raise TimeoutError(f"deadline exceeded at {step}")

            def timeout_for(self, default):
                return min(default, self.remaining())

            def __exit__(self, exc_type, exc, tb):
                self.elapsed = self.clock() - self.start
                self.overrun = self.elapsed > self.seconds
                return False
        """,
        why="""Trace the first test: the deadline starts at 100; checks at 101 and 102 pass; at 104.5 there are 0.5 seconds left, so "generate" passes; at 106 no
        time is left, so "verify" raises with the step named. The exit reads the clock once more (106) and records the overrun. Because the block
        cannot be interrupted, the work itself must cooperate: check before each step, and give each network call at most `timeout_for(...)`
        seconds, so no single call can blow the whole budget (7.4). Starting the clock at `__enter__` rather than `__init__` measures exactly the
        block. Request handlers use exactly this to keep a RAG pipeline within the latency budget promised to users."""),
    predict("Capturing printed output", "medium",
        code="""
        import io, contextlib

        def noisy_library(n):
            print(f"loading {n} shards")
            for i in range(n):
                print(f"shard {i} ok")
            return n * 10

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = noisy_library(2)
        lines = buf.getvalue().splitlines()
        print(result, lines[0], len(lines))

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            import sys
            print("warning: slow", file=sys.stderr)
        print(repr(err.getvalue()))
        """,
        hints=["`redirect_stdout` replaces `sys.stdout` for the block; `print(..., file=sys.stderr)` writes to stderr, which `redirect_stderr` captures."],
        why="""While stdout is redirected, every `print` inside the library goes into the buffer, so its three lines are captured and the function's return value
        is unaffected. The same works for stderr, where warnings and progress messages often go. This is how you silence or record chatty
        libraries, and how tests check printed output; note that it captures Python-level writes only, not output written directly by C
        extensions."""),
)

section("hard", "Hard",
    write("A resource pool", "hard", tag="GenAI",
        prompt="""Write a class `Pool(factory, size)` lending out up to `size` resources created by `factory()`. `acquire()` returns a context manager: entering it
        hands out an idle resource (creating one if fewer than `size` exist; raise `RuntimeError("pool exhausted")` if all are busy); exiting returns
        it to the idle list, **except** when the block raised `ConnectionError`, in which case the resource is discarded (its `close()` is called) so
        a fresh one is created later. Track `created`, and `close()` the pool by closing every idle resource. Exceptions propagate.""",
        code="""
        from contextlib import contextmanager

        class Pool:
            pass
        """,
        tests="""
        made = []
        class Conn:
            def __init__(self):
                self.id = len(made)
                self.closed = False
                made.append(self)
            def close(self):
                self.closed = True

        pool = Pool(Conn, size=2)
        with pool.acquire() as a:
            with pool.acquire() as b:
                assert (a.id, b.id) == (0, 1)
                try:
                    with pool.acquire():
                        pass
                    assert False
                except RuntimeError as e:
                    assert str(e) == "pool exhausted"
        with pool.acquire() as c:
            assert c.id in (0, 1) and pool.created == 2
        try:
            with pool.acquire() as broken:
                raise ConnectionError("dropped")
        except ConnectionError:
            pass
        assert broken.closed and pool.created == 2
        with pool.acquire() as x, pool.acquire() as y:
            assert pool.created == 3 and broken not in (x, y)
        try:
            with pool.acquire() as fine:
                raise ValueError("bad input")
        except ValueError:
            pass
        assert not fine.closed
        pool.close()
        assert all(c.closed for c in made)
        """,
        hints=["Keep `self._idle` (a list) and `self._busy` (a set of ids or a count). `acquire` is a `@contextmanager` method.",
               "In the generator: get a resource, then `try: yield res` / `except ConnectionError: discard; raise` / `else` or `finally`: return it to the idle list if not discarded."],
        solution="""
        from contextlib import contextmanager

        class Pool:
            def __init__(self, factory, size):
                self.factory = factory
                self.size = size
                self._idle = []
                self._busy = 0
                self.created = 0

            def _take(self):
                if self._idle:
                    res = self._idle.pop()
                elif self._busy + len(self._idle) < self.size:
                    res = self.factory()
                    self.created += 1
                else:
                    raise RuntimeError("pool exhausted")
                self._busy += 1
                return res

            @contextmanager
            def acquire(self):
                res = self._take()
                try:
                    yield res
                except ConnectionError:
                    self._busy -= 1
                    res.close()
                    raise
                except BaseException:
                    self._busy -= 1
                    self._idle.append(res)
                    raise
                else:
                    self._busy -= 1
                    self._idle.append(res)

            def close(self):
                while self._idle:
                    self._idle.pop().close()
        """,
        why="""Lending is a scope, so `acquire` is a context manager: the resource is always returned, however the block ends. The pool distinguishes **why** the
        block failed: a `ConnectionError` means the resource itself is probably broken, so it is closed and dropped, and the next borrower gets a
        fresh one (the third connection created); any other error, such as bad input, says nothing about the resource, which goes back to the idle
        list. Counting busy resources keeps the total bounded by `size`, and an exhausted pool fails loudly rather than creating unlimited
        connections. A real pool would wait (with a timeout) instead of raising, and protect its state with a lock for threads or an
        `asyncio.Lock` for tasks (14.5)."""),
    fix("Read the code: a temporary workspace", "hard", tag="ML",
        prompt="""`workspace(env)` should create a temporary directory, make it the current directory, set the given environment variables, and on exit restore
        the previous directory, restore or remove the variables, and delete the directory, **even if the block raises**. After a failure the process
        stays in the deleted directory, the variables leak, and the directory is not removed. Read it, find the bugs and fix them with `ExitStack`
        (or `try`/`finally`).""",
        code="""
        import os, shutil, tempfile
        from contextlib import contextmanager


        @contextmanager
        def workspace(env):
            path = tempfile.mkdtemp()
            old_cwd = os.getcwd()
            os.chdir(path)
            old_env = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            yield path
            for k, v in old_env.items():
                if v is not None:
                    os.environ[k] = v
            os.chdir(old_cwd)
            shutil.rmtree(path)
        """,
        tests="""
        import os
        os.environ.pop("RUN_ID", None)        # a clean slate, even after running the buggy version
        start = os.getcwd()
        os.environ["KEEP_ME"] = "yes"
        with workspace({"RUN_ID": "r1", "KEEP_ME": "temp"}) as path:
            assert os.getcwd() == path and os.environ["RUN_ID"] == "r1" and os.environ["KEEP_ME"] == "temp"
            open("scratch.txt", "w").close()
        assert os.getcwd() == start and "RUN_ID" not in os.environ and os.environ["KEEP_ME"] == "yes" and not os.path.exists(path)
        try:
            with workspace({"RUN_ID": "r2"}) as path2:
                raise RuntimeError("training crashed")
        except RuntimeError:
            pass
        assert os.getcwd() == start and "RUN_ID" not in os.environ and not os.path.exists(path2)
        """,
        hints=["Register each undo step on an `ExitStack` right after the change it undoes: `stack.callback(shutil.rmtree, path)`, `stack.callback(os.chdir, old_cwd)`, and a callback that restores the environment.",
               "Variables that did not exist before must be removed with `os.environ.pop(k, None)`."],
        solution="""
        import os, shutil, tempfile
        from contextlib import ExitStack, contextmanager


        def _restore_env(old_env):
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


        @contextmanager
        def workspace(env):
            with ExitStack() as stack:
                path = tempfile.mkdtemp()
                stack.callback(shutil.rmtree, path, ignore_errors=True)
                old_cwd = os.getcwd()
                os.chdir(path)
                stack.callback(os.chdir, old_cwd)
                old_env = {k: os.environ.get(k) for k in env}
                os.environ.update(env)
                stack.callback(_restore_env, old_env)
                yield path
        """,
        why="""Three bugs. With no `finally`, an exception in the block was raised at the `yield` and every line after it was skipped: the process stayed in a
        directory that would never be deleted, and the variables stayed set, so the next run in the same process inherited `RUN_ID=r2`. The
        environment restore also only handled variables that existed before (`if v is not None`), so a new variable like `RUN_ID` was never
        removed even on success. Registering each undo on an `ExitStack` immediately after the change it reverses fixes everything at once: the
        undos run in reverse order (restore the environment, go back to the old directory, then delete the temporary one, which must not be the
        current directory on some systems), on success and on failure, and if a later setup step fails, only the steps already done are undone.
        `ignore_errors=True` keeps a cleanup failure from masking the original exception."""),
    write("Undo completed steps when a later one fails", "hard", tag="GenAI",
        prompt="""An agent action may involve several steps with side effects (create a ticket, reserve stock, send a notification), and if a later step fails,
        the earlier ones must be undone: a **compensating action** for each. Write `run_saga(steps)` where each step is a `(name, do, undo)` triple:
        `do()` performs the step and returns a result; `undo(result)` reverses it. Run the steps in order; return the list of results if all succeed.
        If a step raises, run the undo of every **completed** step in reverse order (using `ExitStack` callbacks), then re-raise the error with the
        note `"rolled back: <names>"`. An undo that itself raises must not stop the other undos; record it in another note.""",
        code="""
        from contextlib import ExitStack

        def run_saga(steps):
            pass
        """,
        tests="""
        log = []
        def step(name, fail=False, undo_fails=False):
            def do():
                if fail:
                    raise RuntimeError(f"{name} failed")
                log.append(f"do {name}")
                return f"{name}-result"
            def undo(result):
                if undo_fails:
                    raise OSError(f"cannot undo {name}")
                log.append(f"undo {result}")
            return (name, do, undo)

        assert run_saga([step("ticket"), step("reserve")]) == ["ticket-result", "reserve-result"]
        assert log == ["do ticket", "do reserve"]
        log.clear()
        try:
            run_saga([step("ticket"), step("reserve"), step("notify", fail=True)])
            assert False
        except RuntimeError as e:
            assert str(e) == "notify failed" and e.__notes__ == ["rolled back: reserve, ticket"]
        assert log == ["do ticket", "do reserve", "undo reserve-result", "undo ticket-result"]
        log.clear()
        try:
            run_saga([step("ticket"), step("reserve", undo_fails=True), step("notify", fail=True)])
            assert False
        except RuntimeError as e:
            assert e.__notes__ == ["rolled back: reserve, ticket", "undo of reserve failed: OSError: cannot undo reserve"]
        assert log == ["do ticket", "do reserve", "undo ticket-result"]
        """,
        hints=["Inside `with ExitStack() as stack:`, after each successful `do`, register `stack.callback(safe_undo, name, undo, result)`.",
               "On success, `stack.pop_all()` so no undo runs. On failure, let the stack unwind inside a `try`, then add notes and re-raise."],
        solution="""
        from contextlib import ExitStack

        def run_saga(steps):
            completed, undo_errors = [], []

            def safe_undo(name, undo, result):
                try:
                    undo(result)
                except Exception as e:
                    undo_errors.append(f"undo of {name} failed: {type(e).__name__}: {e}")

            try:
                with ExitStack() as stack:
                    results = []
                    for name, do, undo in steps:
                        result = do()
                        results.append(result)
                        completed.append(name)
                        stack.callback(safe_undo, name, undo, result)
                    stack.pop_all()
                    return results
            except Exception as e:
                e.add_note("rolled back: " + ", ".join(reversed(completed)))
                for note in undo_errors:
                    e.add_note(note)
                raise
        """,
        why="""Each completed step registers its undo on the stack, so the stack always holds exactly the compensations needed for the work done so far, in the right
        reverse order. On success, `pop_all()` discards them (the work is kept); on failure, leaving the `with` block runs them all before the
        error reaches the handler that adds the notes. Wrapping each undo in `safe_undo` means one failed compensation is recorded rather than
        aborting the others, and the original error stays the one the caller sees, with the rollback story attached as notes (7.2). This is the
        "saga" pattern used in distributed systems where no single transaction can cover every step, and it is how a careful agent framework
        should treat tool calls with side effects."""),
    predict("Errors while the stack unwinds", "hard",
        code="""
        from contextlib import ExitStack, contextmanager, suppress

        def bad_cleanup():
            raise OSError("cleanup failed")

        try:
            with ExitStack() as stack:
                stack.callback(print, "  first registered, last to run")
                stack.callback(bad_cleanup)
                raise ValueError("original")
        except Exception as e:
            print(type(e).__name__, "| context:", type(e.__context__).__name__)

        with ExitStack() as stack:
            stack.enter_context(suppress(KeyError))
            stack.callback(print, "  callback after suppress")
            {}["missing"]
        print("continued")
        """,
        hints=["If a cleanup raises while another exception is in flight, the new exception replaces it and keeps the old one as context.",
               "A manager on the stack that suppresses an exception stops it for everything registered before it."],
        why="""The stack unwinds in reverse: `bad_cleanup` runs first and raises `OSError` while the `ValueError` is propagating, so the `OSError` replaces it, with
        the original attached as `__context__` (7.2); the print callback still runs afterwards, because the stack keeps unwinding. That is why
        cleanup code should not raise, or should catch and record its own errors (as the saga did). In the second block, the `KeyError` first reaches
        the callback (registered last, so it runs first), then the `suppress` manager, which swallows it, so execution continues after the
        `with`."""),
)

section("interview", "Interview questions",
    explain("What is `contextlib.ExitStack` for? Give concrete uses.", "medium", tag="Interview",
        why="""It manages a set of context managers and cleanup callbacks that is only known at run time, unwinding all of them in reverse order when the block
        exits, on success or failure, like an arbitrary number of nested `with` statements. Uses: opening a variable number of files or connections
        (if one fails, the ones already opened are closed); entering optional context managers without combinatorial `if` branches; registering
        arbitrary undo steps with `callback`, such as deleting temporary files, restoring environment variables or the working directory, or
        compensating completed side effects when a later step fails; and acquiring several resources safely then transferring ownership to the
        caller with `pop_all()`, which returns a new stack holding them. `AsyncExitStack` is the asynchronous counterpart for `async with`
        resources."""),
    explain("Why should you not rely on `__del__` to release resources?", "medium", tag="Interview",
        why="""`__del__` runs when the object is about to be destroyed, which depends on the garbage collector, not on your program's logic. In CPython it usually
        runs when the last reference disappears, but reference cycles delay it until a collection, other interpreters (PyPy) collect at arbitrary
        times, a stored traceback or a cache can keep the object alive indefinitely, and at interpreter shutdown it may never run, or run when
        modules it depends on are already torn down. Exceptions raised inside it are ignored with a warning, so failures are invisible. Resources such
        as connections, file handles and locks therefore leak or are held far longer than intended. Release them deterministically with `with`
        or explicit `close()` calls (and `try`/`finally`), and if a safety net is needed, use `weakref.finalize`, which is more predictable and can
        be run explicitly."""),
    explain("Design the resource lifecycle of an LLM-backed web service.", "hard", tag="Interview",
        why="""Separate resources by lifetime. **Application scope**: one LLM SDK client per provider (each holding an HTTP connection pool), database and vector
        store pools, the tokenizer and any loaded models, created once at start-up and closed at shutdown through the framework's lifespan context
        manager, using an `ExitStack` (or `AsyncExitStack`) so that if one fails to initialise, the others are cleaned up. **Request scope**: a
        tracing span, a deadline, a token budget, a database session or transaction, entered with `with` per request (often as framework
        dependencies with cleanup), so they close even when the client disconnects and the request task is cancelled. **Stream scope**: streaming
        responses as context managers, closed when the consumer stops, so the upstream connection is released and billing stops. Avoid creating
        clients per request, never rely on `__del__`, make `close()` idempotent, discard broken pooled connections, set timeouts on everything,
        and make temporary global state impossible by passing configuration explicitly. Test the lifecycle with fakes that count opens and closes,
        including on failures and cancellations, and monitor pool usage in production to catch leaks."""),
)

recap(
    "`ExitStack` manages a run-time number of managers and callbacks, unwinding them in reverse; `pop_all()` hands them over without closing.",
    "`contextlib` helpers: `suppress` for specific errors, `nullcontext` for optional managers, `closing` for objects with `close()`, `redirect_stdout` to capture prints.",
    "Classes that own a resource offer an idempotent `close()`, `__enter__`/`__exit__`, and a clear error after closing; never rely on `__del__`.",
    "Temporary global state (random seeds, env vars, cwd) is saved and restored exactly, in `finally`; better still, avoid global state.",
    "Budgets and deadlines are cooperative scopes in synchronous code; pools lend resources per block and discard broken ones; sagas register undo steps as they go.",
)
