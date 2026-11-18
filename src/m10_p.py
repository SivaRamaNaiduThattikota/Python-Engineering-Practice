from lesson import *

lesson(
    id="m10-p", num="10.P", title="Module 10 practice set and mini project",
    intro="Mixed problems from all of Module 10: iterator classes and re-iterable containers, context managers written as "
          "classes and generators, and resource patterns with `ExitStack`. Then a mini project that needs all of it: a "
          "streaming export job that opens several sources, batches their records lazily and writes them transactionally.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project export job sources sink transaction exitstack batcher iterator context manager stream tee atomic epochs dataset server lifecycle",
)

section("how", "How to use this page",
    p("""For anything that is iterated, ask: **one pass or many?** Containers hand out a fresh iterator each time (usually from a generator `__iter__`); streams
    are their own iterator and are used once (10.1). For anything that is acquired, ask: **who releases it, and when?** Tie the release to a scope
    with a context manager, put cleanup in `finally`, suppress nothing by accident (10.2), and use `ExitStack` when the number of resources or
    undo steps is decided at run time (10.3)."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all three in one job of the kind data and LLM pipelines run every
    day."""),
)

section("set", "Practice set",
    predict("Iterators inside a with block", "easy",
        code="""
        from contextlib import contextmanager

        @contextmanager
        def source(items):
            print("  open")
            try:
                yield iter(items)
            finally:
                print("  close")

        with source([1, 2, 3]) as it:
            print(next(it), list(it))
        with source("ab") as it:
            for ch in it:
                print("got", ch)
                break
        print(list(it))
        """,
        hints=["The context manager yields a one-shot iterator. Leaving the `with` block closes the source, but the list iterator itself still works."],
        why="""The first block takes one item with `next` and drains the rest with `list`, then closes. The second loop breaks after one item; the `with` then exits
        and prints "close". The yielded object was a plain list iterator, so it can still produce the remaining item after the block, which shows that
        "closing a source" only means what the manager makes it mean: a real file iterator would raise `ValueError` when read after closing."""),
    write("A reader that counts what it consumed", "easy", tag="Data work",
        prompt="""Write a context manager class `CountingReader(lines)` whose `__enter__` returns the reader itself, which is an **iterator** over the non-blank
        lines (stripped). It counts `self.consumed` (lines yielded) and `self.skipped` (blank lines passed over). `__exit__` sets `self.closed = True`
        and propagates exceptions. Iterating after the block raises `ValueError("reader is closed")`.""",
        code="""
        class CountingReader:
            pass
        """,
        tests="""
        with CountingReader(["a", "", "  b ", "   ", "c"]) as r:
            first = next(r)
            rest = list(r)
        assert (first, rest, r.consumed, r.skipped, r.closed) == ("a", ["b", "c"], 3, 2, True)
        try:
            next(r)
            assert False
        except ValueError as e:
            assert str(e) == "reader is closed"
        with CountingReader([]) as empty:
            assert list(empty) == []
        assert iter(r) is r and empty.consumed == 0
        """,
        hints=["Keep `self._it = iter(lines)`; `__next__` loops, counting blanks, until it finds a non-blank line (or `StopIteration` propagates)."],
        solution="""
        class CountingReader:
            def __init__(self, lines):
                self._it = iter(lines)
                self.consumed = 0
                self.skipped = 0
                self.closed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.closed = True
                return False

            def __iter__(self):
                return self

            def __next__(self):
                if self.closed:
                    raise ValueError("reader is closed")
                for line in self._it:
                    if line.strip():
                        self.consumed += 1
                        return line.strip()
                    self.skipped += 1
                raise StopIteration
        """,
        why="""The class is both a context manager (its scope) and an iterator (its content), like a file object. Looping over the shared `self._it` inside
        `__next__` keeps the position across calls, and the `for` loop simply continues where the last call stopped. When the source runs out, the
        method raises `StopIteration` explicitly, the correct signal for an iterator class (unlike a generator, 10.1). Raising `ValueError` after
        close mirrors files ("I/O operation on closed file") and turns use-after-close into a clear error. The counters make it easy to report how
        much of an input a job actually processed."""),
    fix("A manager whose as-target is None", "easy", tag="GenAI",
        prompt="""`ChatScope` should give the block a list to collect messages in, and on exit store them in `self.saved` (only if the block succeeded). The block
        crashes with `AttributeError: 'NoneType' object has no attribute 'append'`. Fix it.""",
        code="""
        class ChatScope:
            def __init__(self):
                self.saved = []

            def __enter__(self):
                self.buffer = []

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    self.saved.extend(self.buffer)
                return False
        """,
        tests="""
        scope = ChatScope()
        with scope as msgs:
            msgs.append("hi")
            msgs.append("refund?")
        assert scope.saved == ["hi", "refund?"]
        try:
            with scope as msgs:
                msgs.append("lost")
                raise TimeoutError("model timeout")
        except TimeoutError:
            pass
        assert scope.saved == ["hi", "refund?"]
        """,
        hints=["`as` receives the **return value** of `__enter__`."],
        solution="""
        class ChatScope:
            def __init__(self):
                self.saved = []

            def __enter__(self):
                self.buffer = []
                return self.buffer

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    self.saved.extend(self.buffer)
                return False
        """,
        why="""`with scope as msgs` binds `msgs` to whatever `__enter__` returns, and a method without a `return` returns `None`, so the block received `None` instead
        of the buffer (10.2). Returning the buffer gives the block exactly the object it should write to, while the manager keeps a reference and
        decides at exit what to keep: committed on success, discarded on failure, the transaction pattern in miniature."""),
    predict("ExitStack with a generator source", "medium",
        code="""
        from contextlib import ExitStack, contextmanager

        @contextmanager
        def opened(name, items):
            print(f"  open {name}")
            try:
                yield (f"{name}:{x}" for x in items)
            finally:
                print(f"  close {name}")

        with ExitStack() as stack:
            streams = [stack.enter_context(opened(n, items)) for n, items in [("a", [1, 2]), ("b", [3])]]
            merged = [x for s in streams for x in s]
            again = [x for s in streams for x in s]
        print(merged, again)
        """,
        hints=["The managers close in reverse order. Generator expressions are one-shot."],
        why="""Both sources are opened in order and closed in reverse when the stack exits. The first comprehension drains both generator expressions; the second
        finds them exhausted and produces nothing, the one-shot rule of 6.3 and 10.1: a stream handed out by a resource can be read once, so code
        that needs two passes must keep the values (here, `merged`) rather than re-reading the streams."""),
    write("Epochs over a dataset", "medium", tag="ML",
        prompt="""Write a class `Epochs(rows, batch_size, epochs, seed)` that is **re-iterable** and yields `(epoch, batch)` pairs: for each epoch from 0, it
        shuffles a copy of the rows with `random.Random(seed + epoch)` (so every epoch has its own, reproducible order), then yields batches of
        `batch_size` rows (the last may be shorter). `len()` returns the total number of batches across all epochs, computed arithmetically. The
        original `rows` must never be reordered.""",
        code="""
        import random

        class Epochs:
            pass
        """,
        tests="""
        rows = list(range(5))
        e = Epochs(rows, batch_size=2, epochs=2, seed=10)
        first = list(e)
        assert first == list(e) and len(e) == 6 and len(first) == 6
        assert [ep for ep, _ in first] == [0, 0, 0, 1, 1, 1]
        epoch0 = [x for ep, b in first if ep == 0 for x in b]
        epoch1 = [x for ep, b in first if ep == 1 for x in b]
        assert sorted(epoch0) == rows and sorted(epoch1) == rows and epoch0 != epoch1
        assert [len(b) for _, b in first[:3]] == [2, 2, 1] and rows == [0, 1, 2, 3, 4]
        assert epoch0 == [x for ep, b in Epochs(rows, 3, 1, 10) for x in b]
        """,
        hints=["`__iter__` is a generator: for each epoch, `order = list(self.rows)`; `random.Random(self.seed + epoch).shuffle(order)`; then slice.",
               "Batches per epoch: `(n + batch_size - 1) // batch_size`."],
        solution="""
        import random

        class Epochs:
            def __init__(self, rows, batch_size, epochs, seed):
                self.rows = list(rows)
                self.batch_size = batch_size
                self.epochs = epochs
                self.seed = seed

            def __len__(self):
                per_epoch = (len(self.rows) + self.batch_size - 1) // self.batch_size
                return per_epoch * self.epochs

            def __iter__(self):
                for epoch in range(self.epochs):
                    order = list(self.rows)
                    random.Random(self.seed + epoch).shuffle(order)
                    for start in range(0, len(order), self.batch_size):
                        yield epoch, order[start:start + self.batch_size]
        """,
        why="""A private `random.Random` per epoch makes the shuffle reproducible (the same seed always gives the same order, so two iterations of the object
        agree), different between epochs, and independent of the global generator (10.3). The shuffle of epoch 0 does not depend on the batch size,
        which the last test checks by regrouping the same order into batches of 3. Shuffling a **copy** leaves the caller's rows untouched (2.4).
        The generator `__iter__` makes the object re-iterable, and `len` is cheap arithmetic, so a training loop can show progress without
        materialising anything: the job of PyTorch's sampler and `DataLoader` with `shuffle=True` and a seeded generator."""),
    fix("A dataset that works for one epoch only", "medium", tag="ML",
        prompt="""`Dataset` is built from a **generator** that reads records, and the training loop iterates over it once per epoch. The second epoch sees no
        data. Fix the class so it can be iterated any number of times: accept either an iterable or a zero-argument function that returns a fresh
        iterable, and in the function case call it on every iteration.""",
        code="""
        class Dataset:
            def __init__(self, source):
                self.source = source

            def __iter__(self):
                for record in self.source:
                    if record.get("text"):
                        yield record["text"].strip()
        """,
        tests="""
        calls = []
        def read_records():
            calls.append(1)
            yield {"text": " refund "}
            yield {"text": ""}
            yield {"text": "reset"}

        ds = Dataset(read_records)
        epochs = [list(ds) for _ in range(3)]
        assert epochs == [["refund", "reset"]] * 3 and len(calls) == 3
        assert list(Dataset([{"text": "a"}, {"x": 1}])) == ["a"] and list(Dataset([{"text": "a"}])) == ["a"]
        """,
        hints=["`callable(self.source)` tells a factory function from an iterable. Call it at the start of every `__iter__`."],
        solution="""
        class Dataset:
            def __init__(self, source):
                self.source = source

            def __iter__(self):
                records = self.source() if callable(self.source) else self.source
                for record in records:
                    if record.get("text"):
                        yield record["text"].strip()
        """,
        why="""The class was correctly re-iterable in shape (a generator `__iter__`), but the data underneath was a one-shot generator, so every epoch after the
        first iterated an exhausted source: "re-iterable" has to hold all the way down. Taking a **factory** (a function that opens the source
        afresh) instead of the source itself lets each iteration start a new read: a new file handle, a new database query. Lists still work as
        before, since they are re-iterable themselves. This is why frameworks such as Hugging Face `datasets` with streaming, or `tf.data`, describe
        data as a recipe to produce records rather than as an already-open stream."""),
    trace("Resources, a stream and a failure", "medium",
        prompt="Fill in `log` after each marked line.",
        code="""
        from contextlib import ExitStack, contextmanager
        log = []

        @contextmanager
        def resource(name):
            log.append(f"open {name}")
            try:
                yield name
            finally:
                log.append(f"close {name}")

        def numbers():
            try:
                for i in range(3):
                    yield i
            finally:
                log.append("stream closed")

        with ExitStack() as stack:
            stack.enter_context(resource("db"))
            gen = numbers()
            stack.callback(gen.close)
            for n in gen:
                if n == 1:
                    break
            log.append(f"stopped at {n}")  # row: "inside, after break"
        log.append("end")  # row: "after the with"
        """,
        trace_vars=["log"],
        hints=["Breaking out of a `for` does not close a generator held in a variable. The stack's callback closes it at the end."],
        why="""The loop stops early but the generator object `gen` is still referenced, so it is merely paused, not closed: its `finally` has not run yet when "stopped
        at 1" is logged. At the end of the `with`, the stack unwinds in reverse: first the callback closes the generator (running its `finally`), then
        the database resource closes. Registering `gen.close` makes the cleanup of a half-consumed stream deterministic instead of waiting for garbage
        collection."""),
    write("Tee a stream into a file, atomically", "hard", tag="GenAI",
        prompt="""Write a generator function `tee_to_file(chunks, path)` that yields every chunk unchanged while writing it to a temporary file next to `path`. Only if the
        stream is consumed to the end does the temporary file replace `path` (`os.replace`). If the consumer stops early (the generator is closed) or
        the source raises, the temporary file is removed, `path` is left untouched, and an error from the source propagates.""",
        code="""
        import os

        def tee_to_file(chunks, path):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "answer.txt")
        assert "".join(tee_to_file(["Refunds ", "take ", "5 days."], p)) == "Refunds take 5 days."
        assert open(p, encoding="utf-8").read() == "Refunds take 5 days."

        g = tee_to_file(["New ", "partial ", "answer"], p)
        assert next(g) == "New "
        g.close()
        assert open(p, encoding="utf-8").read() == "Refunds take 5 days." and sorted(os.listdir(d)) == ["answer.txt"]

        def broken():
            yield "a"
            raise ConnectionError("stream dropped")
        try:
            list(tee_to_file(broken(), p))
            assert False
        except ConnectionError:
            pass
        assert open(p, encoding="utf-8").read() == "Refunds take 5 days." and sorted(os.listdir(d)) == ["answer.txt"]
        """,
        hints=["Open the temporary file, then `try:` loop over the chunks writing and yielding each; after the loop (normal end), close and `os.replace`.",
               "Use `except BaseException:` (which includes the `GeneratorExit` sent by `close()`) to close, remove the temporary file, and `raise`."],
        solution="""
        import os

        def tee_to_file(chunks, path):
            tmp = path + ".part"
            f = open(tmp, "w", encoding="utf-8")
            try:
                for chunk in chunks:
                    f.write(chunk)
                    yield chunk
            except BaseException:
                f.close()
                os.remove(tmp)
                raise
            f.close()
            os.replace(tmp, path)
        """,
        why="""The generator keeps the file open exactly as long as the stream is being consumed (6.3), and three endings are handled differently. A complete
        stream falls out of the loop, so the file is closed and atomically swapped into place. A consumer that stops early closes the generator,
        which raises `GeneratorExit` at the paused `yield`; it is a `BaseException`, so the cleanup branch removes the partial file and re-raises
        it, as generators must. A source error takes the same branch and reaches the caller. Saving a streamed LLM answer this way means a
        cancelled or failed request never leaves a truncated answer on disk that a later step might mistake for a complete one."""),
    fix("Read the code: a model server's resources", "hard", tag="GenAI",
        prompt="""`Server` should create **one** client when it starts (`with Server(make_client) as s:`) and close it when it stops; `handle(prompt)` streams a reply
        and returns the joined text; `handle_first(prompt, n)` returns the first `n` chunks and must close the stream so the provider stops sending.
        The current code creates a client per request, never closes clients when a request fails, and leaves streams open. Read it, find the bugs and
        fix them. (Streams are context managers that are also iterable.)""",
        code="""
        class Server:
            def __init__(self, make_client):
                self.make_client = make_client

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def handle(self, prompt):
                client = self.make_client()
                stream = client.stream(prompt)
                text = "".join(stream)
                client.close()
                return text

            def handle_first(self, prompt, n):
                client = self.make_client()
                stream = client.stream(prompt)
                chunks = []
                for chunk in stream:
                    chunks.append(chunk)
                    if len(chunks) == n:
                        break
                return chunks
        """,
        tests="""
        events = []

        class FakeStream:
            def __init__(self, prompt, fail=False):
                self.chunks, self.fail = prompt.split(), fail
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                events.append("stream closed")
                return False
            def __iter__(self):
                for i, c in enumerate(self.chunks):
                    if self.fail and i == 1:
                        raise ConnectionError("dropped")
                    yield c

        class FakeClient:
            def __init__(self):
                events.append("client created")
            def stream(self, prompt):
                return FakeStream(prompt, fail="FAIL" in prompt)
            def close(self):
                events.append("client closed")

        results = []
        with Server(FakeClient) as s:
            results.append(s.handle("a b c"))
            results.append(s.handle_first("x y z", 2))
            try:
                s.handle("FAIL now please")
                results.append("no error")
            except ConnectionError:
                results.append("error propagated")
        assert results == ["abc", ["x", "y"], "error propagated"]
        assert events == ["client created", "stream closed", "stream closed", "stream closed", "client closed"]
        """,
        hints=["Create the client in `__enter__`, close it in `__exit__`; requests use `self.client`.",
               "Use `with self.client.stream(prompt) as stream:` in both handlers, so the stream is closed on success, on early exit and on error."],
        solution="""
        class Server:
            def __init__(self, make_client):
                self.make_client = make_client
                self.client = None

            def __enter__(self):
                self.client = self.make_client()
                return self

            def __exit__(self, *exc):
                if self.client is not None:
                    self.client.close()
                    self.client = None
                return False

            def handle(self, prompt):
                with self.client.stream(prompt) as stream:
                    return "".join(stream)

            def handle_first(self, prompt, n):
                chunks = []
                with self.client.stream(prompt) as stream:
                    for chunk in stream:
                        chunks.append(chunk)
                        if len(chunks) == n:
                            break
                return chunks
        """,
        why="""Three resource bugs, each a lesson of this module. **A client per request** means a new connection pool per call, slow and wasteful; the client's
        lifetime belongs to the server's scope, so it is created in `__enter__` and closed in `__exit__` (10.3). **Cleanup skipped on error**: when the
        stream failed, `client.close()` was never reached; now the client's cleanup no longer depends on each request at all. **Streams left open**:
        `handle_first` stopped reading but never closed the stream, so a real provider would keep generating (and billing) the rest of the
        answer; `with ... as stream` closes it on the normal path, after a `break`, and when the stream raises (10.2). The event list in the test
        is the whole lifecycle in order: one client, three streams each closed exactly once, then one client close."""),
    explain("When do you write a generator, an iterator class, or a context manager?", "medium", tag="Interview",
        why="""A **generator** (function or `__iter__` method) is the default for producing a sequence: it is short, lazy, and manages its own position and
        `StopIteration`; containers use a generator `__iter__` to be re-iterable. An **iterator class** with `__next__` is for streams that need more
        than iteration: extra methods (`peek`, `close`), state that other code reads during iteration (text so far, pages fetched), or careful
        control of reading ahead. A **context manager** is about scope, not sequence: something acquired must be released (files, clients, locks,
        transactions, temporary settings), so the release is guaranteed by `__exit__` or a `finally` around a `yield`. They combine naturally: a
        file or SDK stream is both an iterator and a context manager, a generator can hold a `with` open while it yields, and `ExitStack` manages
        several resources whose number is known only at run time."""),
    explain("A user disconnects while your service is streaming an LLM answer. What happens to your resources, and how do you make it safe?", "hard", tag="Interview",
        why="""The web framework notices the disconnect and stops consuming the response generator, typically by closing it (sync) or cancelling the task (async),
        which raises `GeneratorExit` or `CancelledError` at the point where your code is paused. Nothing after that point runs, except `finally`
        blocks and `__exit__` methods: so every resource opened during the request must be scoped with `with` or `try`/`finally`. The upstream LLM
        stream must be closed (the SDK stream as a context manager does it), or the provider keeps generating and billing the full answer;
        temporary files must be removed or committed atomically only on completion; spans and logs should record that the request was cancelled;
        locks and pooled connections must be returned. Do not catch `GeneratorExit` or `CancelledError` and continue, and do not do slow work in
        cleanup. Long-lived resources (the client and its connection pool) belong to the application scope and are unaffected. Test it by closing the
        response generator after a few chunks with fakes that record what was closed, as in the projects of this module."""),
    predict("Everything at once", "hard",
        code="""
        from contextlib import ExitStack, suppress

        class Ticker:
            def __init__(self, n):
                self.n = n
            def __iter__(self):
                for i in range(self.n):
                    yield i

        class Guard:
            def __init__(self, name, log):
                self.name, self.log = name, log
            def __enter__(self):
                self.log.append("+" + self.name)
                return self
            def __exit__(self, exc_type, exc, tb):
                self.log.append("-" + self.name + (f"!{exc_type.__name__}" if exc_type else ""))
                return False

        log = []
        t = Ticker(3)
        with ExitStack() as stack:
            stack.enter_context(Guard("a", log))
            stack.enter_context(suppress(ZeroDivisionError))
            stack.enter_context(Guard("b", log))
            total = sum(t) + sum(t)
            log.append(f"total={total}")
            1 / 0
        log.append("done")
        print(log)
        """,
        hints=["`Ticker` is re-iterable. The stack unwinds in reverse; `suppress` stops the exception for everything registered before it."],
        why="""`Ticker` returns a new generator for each `sum`, so both passes see 0, 1, 2, and the total is 6. The division error unwinds the stack in reverse:
        `b` exits first and sees the exception; `suppress` then swallows it; so `a`, registered before `suppress`, exits normally, and execution
        continues after the block with "done". The position of `suppress` on the stack decides which managers see the error."""),
)

section("project", "Mini project: a streaming export job",
    p("""A nightly job reads records from several sources (files, an API, a database query), skips blank and comment lines, batches the rest and
    writes them to a destination that supports transactions. Every source must be closed however the job ends, the destination must receive
    either everything or nothing, and the job must report what it did. Build it from the pieces of this module."""),
    write("Export records from several sources", "hard", key="export-job", tag="Project",
        prompt="""Implement three classes and a function.

        - **`Source(name, lines)`**: a context manager whose `__enter__` marks it open (appending `f"open {name}"` to a shared `EVENTS` list) and returns
          itself; `__exit__` closes it (appending `f"close {name}"`) and propagates errors; iterating an open source yields `(name, line_number,
          text)` for each line that is not blank and does not start with `#`, stripped, with line numbers counted from 1 over **all** lines.
          Iterating a closed or never-opened source raises `ValueError`.
        - **`Batches(iterable, size)`**: an iterator class yielding lists of up to `size` items lazily, counting `self.made`.
        - **`Destination()`**: a context manager for one transaction: `__enter__` returns itself; `write(batch)` stages a batch; on a clean exit
          the staged batches are appended to `self.committed` and `self.commits` is incremented; on an exception nothing is committed and
          `self.rollbacks` is incremented; errors propagate.
        - **`export(sources, destination, batch_size)`**: inside one `ExitStack`, enter every source and the destination, chain the sources'
          records in order, write them in batches, and return `{"records": n, "batches": b}`. If anything fails, all sources are closed, the
          destination rolls back, and the error propagates with the note `f"export failed after {n} records"`.""",
        code="""
        from contextlib import ExitStack
        from itertools import chain

        EVENTS = []


        class Source:
            pass


        class Batches:
            pass


        class Destination:
            pass


        def export(sources, destination, batch_size):
            pass
        """,
        tests="""
        EVENTS.clear()
        a = Source("crm", ["# header", "ana@x.io", "", "  bo@x.io  "])
        b = Source("shop", ["cy@x.io", "# skip", "dee@x.io", "ed@x.io"])
        dest = Destination()
        stats = export([a, b], dest, batch_size=2)
        assert stats == {"records": 5, "batches": 3}
        assert dest.committed == [[("crm", 2, "ana@x.io"), ("crm", 4, "bo@x.io")], [("shop", 1, "cy@x.io"), ("shop", 3, "dee@x.io")], [("shop", 4, "ed@x.io")]]
        assert dest.commits == 1 and dest.rollbacks == 0
        assert EVENTS == ["open crm", "open shop", "close shop", "close crm"]

        class Exploding(Source):
            def __iter__(self):
                yield from super().__iter__()
                raise ConnectionError("source dropped")

        EVENTS.clear()
        dest2 = Destination()
        try:
            export([Source("ok", ["x", "y", "z"]), Exploding("api", ["p"])], dest2, batch_size=2)
            assert False
        except ConnectionError as e:
            assert e.__notes__ == ["export failed after 4 records"]
        assert dest2.committed == [] and dest2.rollbacks == 1 and dest2.commits == 0
        assert EVENTS == ["open ok", "open api", "close api", "close ok"]

        s = Source("late", ["a"])
        try:
            list(s)
            assert False
        except ValueError:
            pass
        bt = Batches(iter(range(5)), 2)
        assert list(bt) == [[0, 1], [2, 3], [4]] and bt.made == 3 and iter(bt) is bt
        assert export([], Destination(), 3) == {"records": 0, "batches": 0}
        """,
        hints=["`Source.__iter__` can be a generator that first checks `self._open`.",
               "`Batches.__next__` pulls up to `size` items from `self._it` with `next(self._it, sentinel)`.",
               "In `export`, count records by wrapping the chained records in a small generator that increments a counter as items pass; catch exceptions outside the `with ExitStack()` to add the note."],
        solution="""
        from contextlib import ExitStack
        from itertools import chain

        EVENTS = []


        class Source:
            def __init__(self, name, lines):
                self.name = name
                self.lines = list(lines)
                self._open = False

            def __enter__(self):
                self._open = True
                EVENTS.append(f"open {self.name}")
                return self

            def __exit__(self, exc_type, exc, tb):
                self._open = False
                EVENTS.append(f"close {self.name}")
                return False

            def __iter__(self):
                if not self._open:
                    raise ValueError(f"source {self.name} is not open")
                for number, line in enumerate(self.lines, start=1):
                    text = line.strip()
                    if text and not text.startswith("#"):
                        yield self.name, number, text


        _DONE = object()


        class Batches:
            def __init__(self, iterable, size):
                self._it = iter(iterable)
                self.size = size
                self.made = 0

            def __iter__(self):
                return self

            def __next__(self):
                batch = []
                for _ in range(self.size):
                    item = next(self._it, _DONE)
                    if item is _DONE:
                        break
                    batch.append(item)
                if not batch:
                    raise StopIteration
                self.made += 1
                return batch


        class Destination:
            def __init__(self):
                self.committed = []
                self.commits = 0
                self.rollbacks = 0
                self._staged = []

            def __enter__(self):
                self._staged = []
                return self

            def write(self, batch):
                self._staged.append(list(batch))

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    self.committed.extend(self._staged)
                    self.commits += 1
                else:
                    self.rollbacks += 1
                self._staged = []
                return False


        def export(sources, destination, batch_size):
            count = 0

            def counted(records):
                nonlocal count
                for record in records:
                    count += 1
                    yield record

            try:
                with ExitStack() as stack:
                    opened = [stack.enter_context(s) for s in sources]
                    dest = stack.enter_context(destination)
                    batches = Batches(counted(chain.from_iterable(opened)), batch_size)
                    for batch in batches:
                        dest.write(batch)
                    return {"records": count, "batches": batches.made}
            except Exception as e:
                e.add_note(f"export failed after {count} records")
                raise
        """,
        why="""Every lesson of the module has a job here:

        - **Iterator classes (10.1):** `Source` is a re-iterable container whose generator `__iter__` refuses to run while closed; `Batches` is a
          one-shot iterator class because it carries state (`made`) that the job reports; `counted` is a pass-through generator that measures the
          stream without materialising it, and `chain.from_iterable` (6.4) joins the sources lazily, so records flow from source to batch to
          destination one batch at a time.
        - **Context managers (10.2):** sources open and close as scopes, and `Destination` is a transaction: staged batches are committed only on a
          clean exit and discarded on an exception, which still propagates.
        - **Resource patterns (10.3):** one `ExitStack` holds a run-time number of sources plus the destination, so a failure anywhere unwinds
          everything in reverse order, the destination first (rolling back) and then the sources (closing), exactly as the event log shows.

        The note added outside the stack tells the operator how far the job got, without changing the exception type (7.2). In production the
        sources would be file readers, API paginators or database cursors, the destination a database transaction or an atomic file write, and the
        same structure would hold."""),
)

recap(
    "Containers return a fresh iterator per loop (generator `__iter__`); streams are one-shot iterators, and re-iterable data needs a re-openable source all the way down.",
    "Context managers tie release to scope: `as` gets `__enter__`'s return value, cleanup goes in `__exit__` or a `finally` around the `yield`.",
    "Suppress exceptions only on purpose; commit on clean exit, roll back on error, and let the error propagate.",
    "`ExitStack` manages any number of resources and undo callbacks, unwinding in reverse; `pop_all` hands them over.",
    "Close half-consumed streams explicitly; share long-lived clients per application and scope everything else per request.",
)
