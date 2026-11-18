from lesson import *

lesson(
    id="m14-4", num="14.4", title="asyncio basics",
    intro="asyncio runs thousands of waits concurrently in one thread, which is why modern LLM clients, web frameworks such as FastAPI, "
          "and agent frameworks are async. Coroutines and `await`, the event loop, tasks, `gather` and `TaskGroup`, why one blocking "
          "call stalls everything, async iteration and context managers, and how exceptions and cancellation travel. On this site "
          "asyncio runs on simulated time (14.1), so `loop.time()` shows exactly how long concurrent code would take.",
    desc="Coroutines, `await`, tasks and `gather`.",
    keys="asyncio async await coroutine event loop asyncio.run create_task task gather return_exceptions taskgroup exceptiongroup except* sleep loop.time blocking to_thread async for async with async generator asynccontextmanager cancel cancellederror wait first_completed",
)

term("Coroutine", "The object returned by calling an `async def` function. It runs only when awaited or wrapped in a task, and it can pause at each `await`.")
term("Event loop", "The scheduler at the heart of asyncio: it runs one task until it awaits something not ready, then switches to another task that can continue.")
term("Task", "A coroutine scheduled to run concurrently on the event loop, created with `asyncio.create_task`; it can be awaited for its result or cancelled.")

section("coroutines", "Coroutines and await",
    p("""An **`async def`** function does not run when called: it returns a **coroutine** object, a paused computation. Inside it, **`await x`** waits for `x` (another
    coroutine, a task, or a future) and, crucially, lets the event loop run **other** work while `x` is not ready. `asyncio.run(main())` creates an event loop, runs
    the coroutine `main` to completion, and closes the loop; it is the entry point of an async program, called once. Calling a coroutine function without
    awaiting it is a common bug: nothing runs, and Python warns `coroutine ... was never awaited`."""),
    p("""Awaiting one coroutine after another runs them **sequentially**, just like normal function calls; the concurrency comes from scheduling several at once,
    as **tasks**. `asyncio.create_task(coro)` schedules a coroutine to start as soon as the current task yields to the loop, and returns a `Task` you can await
    later. `await asyncio.gather(a, b, c)` runs several awaitables concurrently and returns their results **in argument order**."""),
    ex("""
    import asyncio

    async def call_model(name, seconds):
        await asyncio.sleep(seconds)      # stands in for waiting on the network
        return f"{name} done"

    async def sequential():
        return [await call_model("a", 1), await call_model("b", 2), await call_model("c", 1)]

    async def concurrent():
        return await asyncio.gather(call_model("a", 1), call_model("b", 2), call_model("c", 1))

    async def timed(make):
        loop = asyncio.get_running_loop()
        start = loop.time()
        result = await make()
        return result, loop.time() - start

    print(asyncio.run(timed(sequential)))
    print(asyncio.run(timed(concurrent)))
    print(type(call_model("x", 1)).__name__)
    """, "await_vs_gather.py"),
    p("""The sequential version takes the **sum** of the waits, 4 seconds; with `gather`, all three wait at the same time and the total is the **longest** wait, 2 seconds.
    The last line creates a coroutine and never awaits it, which is exactly the "never awaited" mistake (Python prints a warning)."""),
)

section("loop", "How the event loop runs tasks",
    p("""The event loop keeps a queue of tasks ready to run. It runs one until that task reaches an `await` on something not ready (a sleep, a network read), then
    picks the next ready task. When a timer expires or data arrives, the waiting task becomes ready again. Everything happens in **one thread**, so between two
    `await`s a task runs without interruption: no other task can modify shared state in the middle of a block that contains no `await`. That makes asyncio easier
    to reason about than threads, but it also means a task that never awaits **starves all the others**."""),
    p("""This is the most important rule of asyncio: **never block the event loop**. A call to `time.sleep(2)`, a synchronous HTTP library such as `requests`, a large
    file read, or a CPU-heavy loop inside a coroutine freezes every other task for its duration, so a server stops answering all users while one request
    tokenises a document. Use async libraries (`asyncio.sleep`, `httpx.AsyncClient`, the async clients of the OpenAI and Anthropic SDKs, `aiofiles`), and push
    unavoidable blocking calls to a thread with **`await asyncio.to_thread(fn, *args)`** or CPU work to a process pool with `loop.run_in_executor(pool, fn,
    *args)`."""),
    ex("""
    import asyncio

    events = []

    async def worker(name, steps):
        for i in range(steps):
            events.append(f"{name}{i}")
            await asyncio.sleep(0)          # yield to the loop between steps

    async def hog():
        events.append("hog start")
        total = sum(range(200_000))          # no await: nothing else can run meanwhile
        events.append("hog end")

    async def main():
        await asyncio.gather(worker("a", 3), hog(), worker("b", 3))

    asyncio.run(main())
    print(events)
    """, "loop_order.py"),
    p("""`asyncio.sleep(0)` is a pure "let others run" point, so the workers take turns. The hog starts after `a`'s first step and runs to the end without yielding, so
    everything else waits for it. With a real CPU-heavy function that would be seconds of a frozen server."""),
)

section("structured", "gather, TaskGroup and exceptions",
    p("""If one awaitable passed to `gather` raises, `gather` raises that exception at once, and the other awaitables **keep running** (they are not cancelled);
    with **`return_exceptions=True`**, exceptions are returned in the result list in place of values, which suits batches where each item may fail
    independently. **`asyncio.TaskGroup`** (Python 3.11) is the structured alternative: `async with asyncio.TaskGroup() as tg:` and `tg.create_task(...)` inside;
    the block waits for all tasks, and if any fails, it **cancels the others** and raises an **`ExceptionGroup`** with every failure, which you handle with
    `except*` clauses. Use `TaskGroup` when the tasks belong together (if one fails, the whole operation failed) and `gather(..., return_exceptions=True)` when
    each result stands alone."""),
    p("""Keep a reference to every task you create, and make sure each is awaited: the event loop holds only weak references to tasks, so a "fire and forget" task can
    be garbage-collected before it finishes, and an exception in a task nobody awaits is only reported as "Task exception was never retrieved" when it is
    destroyed. `TaskGroup` handles both for you."""),
)

section("async_with", "async with, async for and async generators",
    p("""Objects whose setup or teardown must wait for I/O use **`async with`**: an HTTP client session, a database connection, a lock (`asyncio.Lock`), a semaphore
    (14.5). `contextlib.asynccontextmanager` turns an async generator with one `yield` into such a context manager, as `@contextmanager` does for sync code (10.2).
    Iterators that wait between items use **`async for`**: an **async generator** is an `async def` containing `yield`, and it can `await` between items. This is
    exactly the shape of **streaming LLM responses**: `async for event in client.messages.stream(...)` receives tokens as they are generated. Async comprehensions
    (`[x async for x in agen()]`) work too."""),
    ex("""
    import asyncio
    from contextlib import asynccontextmanager

    async def stream_reply(text, delay=0.05):
        for token in text.split():
            await asyncio.sleep(delay)       # tokens arrive over time
            yield token

    @asynccontextmanager
    async def connection(log):
        log.append("open")
        try:
            yield "conn"
        finally:
            log.append("close")

    async def main():
        log = []
        async with connection(log) as conn:
            tokens = [t async for t in stream_reply("Refunds take five business days")]
        loop = asyncio.get_running_loop()
        return tokens, log, round(loop.time(), 2)

    print(asyncio.run(main()))
    """, "async_iter.py"),
)

section("cancel", "Cancellation",
    p("""`task.cancel()` asks a task to stop: the next time it is suspended at an `await`, a **`CancelledError`** is raised inside it, so `finally` blocks and `async with`
    exits run its cleanup, and the task ends as cancelled. `CancelledError` derives from `BaseException`, not `Exception`, precisely so that `except Exception:`
    handlers do not swallow it; if you catch it to clean up, re-raise it. Timeouts are built on cancellation: `asyncio.wait_for(aw, timeout)` and `async with
    asyncio.timeout(seconds):` cancel the work when the time is up and raise `TimeoutError` (14.5). `asyncio.shield(aw)` protects an awaitable from being cancelled
    by its caller, for work that must finish (such as saving a result)."""),
)

section("warmup", "Warm-up",
    predict("Sequential awaits versus gather", "easy",
        code="""
        import asyncio

        async def embed(text, seconds):
            await asyncio.sleep(seconds)
            return len(text)

        async def main():
            loop = asyncio.get_running_loop()
            t0 = loop.time()
            a = await embed("refund", 1.0)
            b = await embed("policy", 1.5)
            t1 = loop.time()
            c, d, e = await asyncio.gather(embed("x", 0.5), embed("yy", 2.0), embed("zzz", 1.0))
            t2 = loop.time()
            task = asyncio.create_task(embed("late", 3.0))
            await asyncio.sleep(1.0)
            done_early = task.done()
            f = await task
            t3 = loop.time()
            return (a, b, t1 - t0), (c, d, e, t2 - t1), (done_early, f, t3 - t2)

        print(asyncio.run(main()))
        """,
        hints=["Awaits in sequence add up; `gather` takes as long as its slowest awaitable. A task starts running as soon as the current coroutine awaits."],
        why="""The two sequential awaits take 1.0 + 1.5 seconds. `gather` runs three embeddings at once and returns their results in argument order after the slowest, 2.0
        seconds. The task created before `sleep(1.0)` starts running during that sleep, so it is not done after one second, and awaiting it takes the remaining
        two seconds: the total is still 3.0, because it ran **while** the main coroutine slept."""),
    write("Fetch many pages concurrently", "easy", tag="GenAI",
        prompt="""Write `async def fetch_all(fetch, urls)` that awaits `fetch(url)` for every URL **concurrently** with `asyncio.gather` and returns a dict from URL to result, in input
        order. Then write `run_fetch(fetch, urls)` that runs it with `asyncio.run` and returns `(results, elapsed)` where `elapsed` is measured with the loop's clock.""",
        code="""
        import asyncio

        async def fetch_all(fetch, urls):
            pass

        def run_fetch(fetch, urls):
            pass
        """,
        tests="""
        import asyncio
        async def fetch(url):
            await asyncio.sleep(len(url) / 10)
            return url.upper()
        results, elapsed = run_fetch(fetch, ["a.io", "bb.io", "ccc.io"])
        assert results == {"a.io": "A.IO", "bb.io": "BB.IO", "ccc.io": "CCC.IO"} and list(results) == ["a.io", "bb.io", "ccc.io"]
        assert abs(elapsed - 0.6) < 1e-9
        assert run_fetch(fetch, []) == ({}, 0.0)
        """,
        hints=["`values = await asyncio.gather(*(fetch(u) for u in urls))`, then `dict(zip(urls, values))`.",
               "In `run_fetch`, define an inner `async def main():` that reads `asyncio.get_running_loop().time()` before and after."],
        solution="""
        import asyncio


        async def fetch_all(fetch, urls):
            values = await asyncio.gather(*(fetch(u) for u in urls))
            return dict(zip(urls, values))


        def run_fetch(fetch, urls):
            async def main():
                loop = asyncio.get_running_loop()
                start = loop.time()
                results = await fetch_all(fetch, urls)
                return results, loop.time() - start
            return asyncio.run(main())
        """,
        why="""`gather` schedules every `fetch` at once, so the three waits overlap and the total is the longest one, 0.6 seconds, not the 1.5-second sum. Its results come back in
        argument order, so zipping with `urls` pairs each result with its URL. `asyncio.run` is called once, at the boundary between synchronous and async code; the
        loop's clock (`loop.time()`) is the right way to measure async durations, and on this site it shows the exact simulated time."""),
    fix("Concurrent code that runs one at a time", "easy", tag="GenAI",
        prompt="""`summarise_all` was meant to call the model for all documents at once, but it awaits each call inside the loop, so the calls run one after another. Make the calls
        run concurrently while keeping the results in input order.""",
        code="""
        import asyncio

        async def summarise_all(llm, docs):
            results = []
            for doc in docs:
                results.append(await llm(doc))
            return results
        """,
        tests="""
        import asyncio
        async def llm(doc):
            await asyncio.sleep(2.0)
            return doc[:3]
        async def main():
            loop = asyncio.get_running_loop()
            start = loop.time()
            out = await summarise_all(llm, ["refunds", "shipping", "returns", "warranty"])
            return out, loop.time() - start
        out, elapsed = asyncio.run(main())
        assert out == ["ref", "shi", "ret", "war"]
        assert elapsed == 2.0
        """,
        hints=["Build the coroutines first and await them together: `await asyncio.gather(*(llm(d) for d in docs))`."],
        solution="""
        import asyncio

        async def summarise_all(llm, docs):
            return list(await asyncio.gather(*(llm(doc) for doc in docs)))
        """,
        why="""`await` inside a loop waits for each call to finish before starting the next, so four 2-second calls take 8 seconds; `async` code is not automatically concurrent.
        Creating all the coroutines and handing them to `gather` lets the event loop run them together, and the total becomes 2 seconds. With hundreds of documents,
        unbounded `gather` would hit rate limits, which is what the semaphores of 14.5 are for."""),
    predict("Who runs when", "easy",
        code="""
        import asyncio

        log = []

        async def step(name, n):
            for i in range(n):
                log.append(f"{name}{i}")
                await asyncio.sleep(0)

        async def main():
            t = asyncio.create_task(step("t", 2))
            log.append("created")
            await step("m", 2)
            log.append("main done")
            await t
            log.append("task done")

        asyncio.run(main())
        print(log)
        """,
        hints=["A new task does not start until the current one awaits something. `sleep(0)` yields to the loop."],
        why="""Creating the task only schedules it, so `created` comes first. When `main` reaches its first `sleep(0)`, the loop runs the task's first step, and from then on they
        alternate at each yield. Main finishes its loop before the task's second step completes its yield, and awaiting the task waits for its remaining work."""),
)

section("medium", "Medium",
    write("Classify a batch without losing failures", "medium", tag="GenAI",
        prompt="""Write `async def classify_batch(llm, texts)` that calls `await llm(text)` for all texts concurrently and returns a list, in input order, of `{"text": ..., "label":
        ... or None, "error": None or "ExceptionName: message"}`. One failing call must not affect the others.""",
        code="""
        import asyncio

        async def classify_batch(llm, texts):
            pass
        """,
        tests="""
        import asyncio
        async def llm(text):
            await asyncio.sleep(0.1 * len(text))
            if "timeout" in text:
                raise TimeoutError("model timed out")
            if not text:
                raise ValueError("empty")
            return "spam" if "prize" in text else "ham"
        out = asyncio.run(classify_batch(llm, ["win a prize", "", "timeout please", "lunch?"]))
        assert out == [{"text": "win a prize", "label": "spam", "error": None}, {"text": "", "label": None, "error": "ValueError: empty"},
                       {"text": "timeout please", "label": None, "error": "TimeoutError: model timed out"}, {"text": "lunch?", "label": "ham", "error": None}]
        assert asyncio.run(classify_batch(llm, [])) == []
        """,
        hints=["`await asyncio.gather(*coros, return_exceptions=True)` puts exceptions in the result list.", "Check `isinstance(r, Exception)` for each result."],
        solution="""
        import asyncio


        async def classify_batch(llm, texts):
            results = await asyncio.gather(*(llm(t) for t in texts), return_exceptions=True)
            out = []
            for text, r in zip(texts, results):
                if isinstance(r, Exception):
                    out.append({"text": text, "label": None, "error": f"{type(r).__name__}: {r}"})
                else:
                    out.append({"text": text, "label": r, "error": None})
            return out
        """,
        why="""Without `return_exceptions=True`, the first failure would make `gather` raise, and the successful results would be lost to the caller (while the remaining calls kept
        running in the background). Returning exceptions as values keeps every outcome aligned with its input, the asyncio equivalent of collecting futures in 14.2.
        Checking `Exception` rather than `BaseException` deliberately lets a `CancelledError` propagate, so cancelling the whole batch still works."""),
    fix("Fire-and-forget tasks that never finish", "medium", tag="Data work",
        prompt="""`index_documents` starts one task per document with `create_task`, but never keeps or awaits them, so `main` returns before most tasks finish and some exceptions are
        never seen. Fix it so all tasks complete before it returns, and a failure in any task propagates (use a `TaskGroup`).""",
        code="""
        import asyncio

        async def index_documents(index, docs):
            for doc in docs:
                asyncio.create_task(index(doc))
            return "started"
        """,
        tests="""
        import asyncio
        stored = []
        async def index(doc):
            await asyncio.sleep(0.5)
            if doc == "corrupt":
                raise ValueError("cannot index corrupt")
            stored.append(doc)
        assert asyncio.run(index_documents(index, ["a", "b", "c"])) == "indexed 3"
        assert sorted(stored) == ["a", "b", "c"]
        def failing():
            caught = []
            try:
                asyncio.run(index_documents(index, ["d", "corrupt"]))
            except* ValueError as eg:
                caught.extend(str(e) for e in eg.exceptions)
            return caught
        assert failing() == ["cannot index corrupt"]
        """,
        hints=["`async with asyncio.TaskGroup() as tg:` and `tg.create_task(index(doc))` inside; the block waits for every task.",
               "Return `f\"indexed {len(docs)}\"` after the block. A failure leaves the block as an `ExceptionGroup`."],
        solution="""
        import asyncio

        async def index_documents(index, docs):
            async with asyncio.TaskGroup() as tg:
                for doc in docs:
                    tg.create_task(index(doc))
            return f"indexed {len(docs)}"
        """,
        why="""`create_task` only schedules work; returning without awaiting meant `asyncio.run` finished the program while tasks were still sleeping, so they were cancelled at
        shutdown and their exceptions never reached anyone. The loop also keeps only weak references to tasks, so unreferenced tasks can even disappear mid-flight. A
        `TaskGroup` owns its tasks: the `async with` block does not exit until all have finished, and if one fails the others are cancelled and the failures are raised
        together as an `ExceptionGroup`, handled with `except*`. This is called structured concurrency: no task outlives the block that started it."""),
    trace("Interleavings on the event loop", "medium",
        prompt="Fill in `order` after each marked line.",
        code="""
        import asyncio

        async def job(name, delays, log):
            for d in delays:
                await asyncio.sleep(d)
                log.append(name)

        async def scenario(specs):
            log = []
            await asyncio.gather(*(job(n, ds, log) for n, ds in specs))
            return "".join(log)

        order = asyncio.run(scenario([("a", [1, 1]), ("b", [1.5])]))  # row: "timers"
        order = asyncio.run(scenario([("a", [0, 0]), ("b", [0, 0])]))  # row: "sleep(0) alternation"
        order = asyncio.run(scenario([("a", [2]), ("b", [1]), ("c", [3])]))  # row: "shortest first"
        order = asyncio.run(scenario([("a", [1, 1]), ("b", [2])]))  # row: "a tie at 2 seconds"
        """,
        trace_vars=["order"],
        hints=["A sleeping task becomes ready when its timer expires; at equal times, tasks run in the order their timers were scheduled."],
        why="""Tasks wake in timer order: `a` at 1 and 2 seconds, `b` at 1.5, giving `aba`. With zero delays, every await is a turn, so the tasks alternate in creation order.
        With one sleep each, they finish shortest first. At a tie (both due at 2 seconds), the timer scheduled first fires first: `b` scheduled its 2-second timer at the
        start, before `a` scheduled its second 1-second timer at second 1, so `b` appends before `a`'s second append."""),
    write("Collect a token stream with a limit", "medium", tag="GenAI",
        prompt="""Write `async def collect(stream, max_tokens=None, stop=None)` that consumes an async iterator of tokens with `async for` and returns `(text, reason)`: the tokens joined
        with spaces and `"end"`, `"max_tokens"` (stopped after `max_tokens` tokens) or `"stop"` (a token equal to `stop` was seen; it is not included). When stopping early,
        close the stream with `await stream.aclose()` so its cleanup runs.""",
        code="""
        import asyncio

        async def collect(stream, max_tokens=None, stop=None):
            pass
        """,
        tests="""
        import asyncio
        closed = []
        async def fake_stream(text, delay=0.1):
            try:
                for tok in text.split():
                    await asyncio.sleep(delay)
                    yield tok
            finally:
                closed.append(text)
        text = "Refunds take five business days END extra words"
        assert asyncio.run(collect(fake_stream(text))) == (text, "end")
        assert asyncio.run(collect(fake_stream(text), max_tokens=3)) == ("Refunds take five", "max_tokens")
        assert asyncio.run(collect(fake_stream(text), stop="END")) == ("Refunds take five business days", "stop")
        assert len(closed) == 3
        async def timed():
            loop = asyncio.get_running_loop()
            await collect(fake_stream(text, delay=0.5), max_tokens=2)
            return loop.time()
        assert asyncio.run(timed()) == 1.0
        """,
        hints=["Loop with `async for token in stream:`; check `stop` before appending and `max_tokens` after.",
               "Put `await stream.aclose()` before each early `return`."],
        solution="""
        import asyncio


        async def collect(stream, max_tokens=None, stop=None):
            tokens = []
            async for token in stream:
                if stop is not None and token == stop:
                    await stream.aclose()
                    return " ".join(tokens), "stop"
                tokens.append(token)
                if max_tokens is not None and len(tokens) >= max_tokens:
                    await stream.aclose()
                    return " ".join(tokens), "max_tokens"
            return " ".join(tokens), "end"
        """,
        why="""Streaming model output arrives as an async iterator: each `async for` step awaits the next token, so the loop can serve other users meanwhile, and the caller can
        stop as soon as it has enough, which saves tokens and latency (the timed test shows that collecting two tokens takes only two delays). Closing the stream
        explicitly runs its `finally` block now, which for a real client closes the HTTP connection; otherwise cleanup waits until the generator is garbage-collected
        or the loop shuts down. Stop sequences and token limits are exactly the `finish_reason` values (`"stop"`, `"length"`) that LLM APIs report."""),
    predict("TaskGroup failures and except*", "medium",
        code="""
        import asyncio

        log = []

        async def work(name, seconds, fail=None):
            try:
                await asyncio.sleep(seconds)
                if fail:
                    raise fail(f"{name} failed")
                log.append(f"{name} ok")
            except asyncio.CancelledError:
                log.append(f"{name} cancelled")
                raise

        async def main():
            try:
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(work("fast", 1))
                    tg.create_task(work("bad", 2, ValueError))
                    tg.create_task(work("slow", 5))
            except* ValueError as eg:
                log.append(f"handled {[str(e) for e in eg.exceptions]}")
            return asyncio.get_running_loop().time()

        print(asyncio.run(main()), log)
        """,
        hints=["When a task in a TaskGroup fails, the group cancels the tasks still running and raises an ExceptionGroup when all have stopped."],
        why="""`fast` completes at 1 second. At 2 seconds `bad` raises, so the group cancels `slow`, which sees `CancelledError` at its `await`, logs, and re-raises. The group then
        raises an `ExceptionGroup` containing the `ValueError`, which `except*` handles; the whole operation ended at 2 seconds instead of 5. With `gather`, `slow`
        would have kept running."""),
    write("An async timing context manager", "medium", tag="Data work",
        prompt="""Write an async context manager `timed(label, metrics)` with `contextlib.asynccontextmanager` that measures the duration of its block with the running loop's clock and
        records it in `metrics[label]` as a list of durations (appending), **even if the block raises** (the exception must propagate).""",
        code="""
        import asyncio
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def timed(label, metrics):
            yield
        """,
        tests="""
        import asyncio
        metrics = {}
        async def main():
            async with timed("retrieve", metrics):
                await asyncio.sleep(0.25)
            async with timed("retrieve", metrics):
                await asyncio.sleep(0.5)
            try:
                async with timed("llm", metrics):
                    await asyncio.sleep(1.5)
                    raise TimeoutError("slow")
            except TimeoutError:
                pass
        asyncio.run(main())
        assert metrics == {"retrieve": [0.25, 0.5], "llm": [1.5]}
        assert all(isinstance(v, float) for values in metrics.values() for v in values)
        """,
        hints=["`loop = asyncio.get_running_loop(); start = loop.time()`, then `try: yield` and record in `finally`."],
        solution="""
        import asyncio
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def timed(label, metrics):
            loop = asyncio.get_running_loop()
            start = loop.time()
            try:
                yield
            finally:
                metrics.setdefault(label, []).append(loop.time() - start)
        """,
        why="""`@asynccontextmanager` works like `@contextmanager` (10.2): code before `yield` runs on entry, the block runs at the `yield`, and `finally` runs on exit whether the
        block succeeded or raised, so failed and timed-out calls are measured too, which is important because slow failures are often what you are investigating.
        Measuring with the loop's clock, a monotonic clock, avoids jumps when the system time changes. Wrapping retrieval and model calls like this produces the
        latency metrics that 12.3's structured logs and dashboards report."""),
)

section("hard", "Hard",
    write("Hedged requests: first answer wins", "hard", tag="GenAI",
        prompt="""Tail latency is often fixed by **hedging**: send the same request to two replicas and use whichever answers first. Write `async def first_completed(*coros)` that
        runs the coroutines as tasks, returns the result of the first to **succeed**, cancels the rest, and raises the last exception if all fail. Use `asyncio.wait`
        with `return_when=FIRST_COMPLETED` in a loop.""",
        code="""
        import asyncio

        async def first_completed(*coros):
            pass
        """,
        tests="""
        import asyncio
        log = []
        async def replica(name, seconds, fail=False):
            try:
                await asyncio.sleep(seconds)
                if fail:
                    raise ConnectionError(f"{name} down")
                return name
            except asyncio.CancelledError:
                log.append(f"{name} cancelled")
                raise
        async def main(*coros):
            loop = asyncio.get_running_loop()
            result = await first_completed(*coros)
            return result, loop.time()
        assert asyncio.run(main(replica("eu", 2.0), replica("us", 0.5))) == ("us", 0.5) and log == ["eu cancelled"]
        log.clear()
        assert asyncio.run(main(replica("eu", 1.0, fail=True), replica("us", 3.0))) == ("us", 3.0) and log == []
        try:
            asyncio.run(first_completed(replica("a", 1, True), replica("b", 2, True)))
            assert False
        except ConnectionError as e:
            assert str(e) == "b down"
        """,
        hints=["`pending = {asyncio.create_task(c) for c in coros}`; loop `while pending: done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)`.",
               "For each done task without an exception, cancel the remaining pending tasks and return its result; remember the last exception otherwise."],
        solution="""
        import asyncio


        async def first_completed(*coros):
            pending = {asyncio.create_task(c) for c in coros}
            last_error = None
            try:
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        if task.exception() is None:
                            return task.result()
                        last_error = task.exception()
                raise last_error
            finally:
                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
        """,
        why="""`asyncio.wait(..., FIRST_COMPLETED)` returns as soon as at least one task finishes, with the done and still-pending sets, so the loop can inspect results as they arrive:
        the first success wins, and a failure simply means waiting for the next. The `finally` cancels whatever is still running and waits for those cancellations to
        complete, so no orphaned request keeps consuming a connection or tokens after the function returns (the log shows the slow replica cancelled). Hedging cuts p99
        latency at the cost of extra requests, so production systems usually send the second request only if the first has not answered within, say, the p95 time."""),
    write("Run tasks against a deadline", "hard", tag="RAG",
        prompt="""Write `async def run_with_deadline(jobs, deadline)` where `jobs` maps names to coroutines. Run them all concurrently; when `deadline` seconds have passed, cancel the
        unfinished ones. Return `{"done": {name: result}, "failed": {name: "ExceptionName: message"}, "timed_out": [names, sorted]}`. Use `asyncio.wait(..., timeout=deadline)`.""",
        code="""
        import asyncio

        async def run_with_deadline(jobs, deadline):
            pass
        """,
        tests="""
        import asyncio
        async def retriever(name, seconds, fail=False):
            await asyncio.sleep(seconds)
            if fail:
                raise LookupError(f"{name} index missing")
            return [f"{name}-doc"]
        async def main():
            loop = asyncio.get_running_loop()
            out = await run_with_deadline({"faq": retriever("faq", 0.2), "wiki": retriever("wiki", 1.5), "tickets": retriever("tickets", 0.4, fail=True),
                                           "web": retriever("web", 3.0)}, deadline=1.0)
            return out, loop.time()
        out, t = asyncio.run(main())
        assert out == {"done": {"faq": ["faq-doc"]}, "failed": {"tickets": "LookupError: tickets index missing"}, "timed_out": ["web", "wiki"]}
        assert t == 1.0
        assert asyncio.run(run_with_deadline({}, 1.0)) == {"done": {}, "failed": {}, "timed_out": []}
        """,
        hints=["Create a task per job and keep a dict from task to name; `done, pending = await asyncio.wait(tasks, timeout=deadline)`.",
               "Cancel every pending task and `await asyncio.gather(*pending, return_exceptions=True)` so cancellation completes before returning."],
        solution="""
        import asyncio


        async def run_with_deadline(jobs, deadline):
            names = {asyncio.create_task(coro): name for name, coro in jobs.items()}
            result = {"done": {}, "failed": {}, "timed_out": []}
            if not names:
                return result
            done, pending = await asyncio.wait(names, timeout=deadline)
            for task in done:
                error = task.exception()
                if error is None:
                    result["done"][names[task]] = task.result()
                else:
                    result["failed"][names[task]] = f"{type(error).__name__}: {error}"
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            result["timed_out"] = sorted(names[t] for t in pending)
            return result
        """,
        why="""A RAG service often queries several retrievers and must answer within a latency budget, using whatever arrived in time rather than waiting for the slowest source.
        `asyncio.wait` with a timeout returns at the deadline with the finished and unfinished sets, without raising; finished tasks are split into results and failures,
        and unfinished ones are cancelled and awaited so they stop consuming resources. The whole call ends at exactly 1.0 seconds, as the loop's clock shows. The
        answer can then be generated from the sources that responded, and the timed-out names logged as a degraded-quality signal."""),
    fix("Read the code: an async LLM batch client", "hard", tag="GenAI",
        prompt="""`answer_all` should answer many questions concurrently, but it awaits each call in a loop, uses `gather` elsewhere without `return_exceptions` so one failure loses
        every result, and forgets to `await` the cleanup coroutine, so the client is never closed. Fix it: run all calls concurrently, return `{"answers": [...], "errors":
        {index: "ExceptionName: message"}}` with `None` in place of failed answers, and close the client in a `finally` block with `await client.close()`.""",
        code="""
        import asyncio


        async def answer_all(client, questions):
            answers = []
            for q in questions:
                answers.append(await client.ask(q))
            checks = await asyncio.gather(*(client.moderate(a) for a in answers))
            client.close()
            return {"answers": [a for a, ok in zip(answers, checks) if ok], "errors": {}}
        """,
        tests="""
        import asyncio
        class FakeClient:
            def __init__(self):
                self.closed = False
            async def ask(self, q):
                await asyncio.sleep(1.0)
                if "fail" in q:
                    raise ConnectionError("reset")
                return q.upper()
            async def moderate(self, answer):
                await asyncio.sleep(0.5)
                return True
            async def close(self):
                await asyncio.sleep(0)
                self.closed = True
        async def main():
            client = FakeClient()
            loop = asyncio.get_running_loop()
            out = await answer_all(client, ["refund?", "please fail", "shipping?"])
            return out, loop.time(), client.closed
        out, t, closed = asyncio.run(main())
        assert out == {"answers": ["REFUND?", None, "SHIPPING?"], "errors": {1: "ConnectionError: reset"}}
        assert t == 1.0 and closed
        """,
        hints=["`results = await asyncio.gather(*(client.ask(q) for q in questions), return_exceptions=True)`.",
               "The moderation step is not needed for this specification; wrap the body in `try` and put `await client.close()` in `finally`."],
        solution="""
        import asyncio


        async def answer_all(client, questions):
            try:
                results = await asyncio.gather(*(client.ask(q) for q in questions), return_exceptions=True)
                answers, errors = [], {}
                for i, r in enumerate(results):
                    if isinstance(r, Exception):
                        answers.append(None)
                        errors[i] = f"{type(r).__name__}: {r}"
                    else:
                        answers.append(r)
                return {"answers": answers, "errors": errors}
            finally:
                await client.close()
        """,
        why="""Three classic async mistakes. Awaiting in a loop serialised the calls: three 1-second calls took 3 seconds instead of 1. `gather` without `return_exceptions` turns one
        failed call into an exception that discards every other result. And `client.close()` without `await` only creates a coroutine object, so the connection pool was
        never closed (Python warns "coroutine was never awaited"); in a `finally` it also runs when the batch fails. Keeping failed answers as `None` at their index,
        with errors keyed by index, keeps the output aligned with the questions for retries."""),
    predict("Cancellation in detail", "hard",
        code="""
        import asyncio

        log = []

        async def worker():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                log.append("cleanup")
                raise
            finally:
                log.append("finally")

        async def swallower():
            try:
                await asyncio.sleep(10)
            except Exception:
                log.append("caught by except Exception")
            return "not reached?"

        async def main():
            t = asyncio.create_task(worker())
            await asyncio.sleep(1)
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                log.append(f"cancelled={t.cancelled()}")
            s = asyncio.create_task(swallower())
            await asyncio.sleep(1)
            s.cancel()
            try:
                await s
            except asyncio.CancelledError:
                log.append("swallower cancelled too")
            print(issubclass(asyncio.CancelledError, Exception), issubclass(asyncio.CancelledError, BaseException))
            try:
                await asyncio.wait_for(asyncio.sleep(5), timeout=2)
            except TimeoutError:
                log.append(f"timeout at {asyncio.get_running_loop().time()}")

        asyncio.run(main())
        print(log)
        """,
        hints=["`cancel()` raises `CancelledError` inside the task at its current `await`. `CancelledError` is a `BaseException`, so `except Exception` does not catch it."],
        why="""Cancelling `worker` raises `CancelledError` at its `sleep`, so the handler and the `finally` run, and re-raising lets the task end as cancelled. The `swallower`'s `except
        Exception` does **not** catch `CancelledError`, since Python 3.8 made it a `BaseException`, so cancellation still works through careless handlers. `wait_for`
        cancels the inner sleep after 2 seconds and raises `TimeoutError` (the built-in, which `asyncio.TimeoutError` now aliases), at time 4: one second for each
        earlier sleep plus the two-second timeout."""),
)

section("interview", "Interview questions",
    explain("What is the event loop, and why does a single blocking call hurt an asyncio service so much?", "medium", tag="Interview",
        why="""The event loop is a scheduler running in one thread: it runs a task until that task awaits something not ready, then switches to another ready task, and resumes the
        first when its I/O completes or its timer fires. Concurrency comes entirely from tasks voluntarily yielding at `await` points. A blocking call (`time.sleep`,
        `requests.get`, a synchronous database driver, a big file read, or CPU-heavy code like tokenising a document) never yields, so while it runs **no other task
        makes progress**: every in-flight request on the server stalls, timeouts fire, health checks fail, and latency spikes for all users. The fixes: use async
        libraries end to end, offload unavoidable blocking calls with `asyncio.to_thread` (or a thread pool) and CPU work with a process pool via `run_in_executor`, and
        detect problems with asyncio's debug mode, which logs callbacks that take longer than 100 ms."""),
    explain("asyncio or threads for I/O-bound work: how do you choose?", "medium", tag="Interview",
        why="""Both overlap waits. **Threads** work with any library, including blocking ones, and require no change to the call chain, but each costs memory and OS scheduling, and
        shared state needs locks; tens to a few hundred concurrent operations are comfortable. **asyncio** runs thousands of concurrent operations in one thread with
        little overhead, switches only at explicit `await` points (so fewer data races), and has structured tools for timeouts, cancellation and limits (`TaskGroup`,
        `asyncio.timeout`, semaphores); but every library in the path must be async, async-ness spreads through the call chain ("function colouring"), and one blocking
        call stalls everything. Choose asyncio for high-concurrency network services and LLM batch clients built on async SDKs, or when the framework is async
        (FastAPI, agent frameworks); choose threads for a modest number of calls through synchronous libraries, or to integrate blocking code into async programs via
        `to_thread`."""),
    explain("Compare asyncio.gather and TaskGroup. When would you use each?", "hard", tag="Interview",
        why="""`gather(*aws)` runs awaitables concurrently and returns results in order. By default, the first exception propagates immediately while the other awaitables **keep running**
        unattended; with `return_exceptions=True`, exceptions are returned as values, so it suits independent batch items where each outcome is recorded. `TaskGroup`
        (3.11+) provides **structured concurrency**: tasks are created inside an `async with` block, the block waits for all of them, and on the first failure it cancels the
        rest and raises an `ExceptionGroup` with every exception, handled with `except*`; no task can outlive the block, so there are no orphaned tasks or unretrieved
        exceptions, and cancellation of the parent propagates cleanly. Use `TaskGroup` when the subtasks are parts of one operation that should fail as a whole (fetch
        user, documents and settings to build one response); use `gather(..., return_exceptions=True)` (or tasks inside a group that catch their own errors) when partial
        success is acceptable, such as classifying a batch of messages."""),
)

recap(
    "`async def` returns a coroutine; `await` waits and lets other tasks run; `asyncio.run(main())` is the single entry point.",
    "Concurrency needs tasks: `gather` or `create_task`; awaiting in a loop is sequential. Measure with `loop.time()`.",
    "Never block the event loop: use async libraries, `asyncio.to_thread` for blocking calls, and process pools for CPU work.",
    "`gather(return_exceptions=True)` for independent items; `TaskGroup` for operations that succeed or fail together, with `except*`.",
    "Use `async for` for streams and `async with` for async resources; cancellation raises `CancelledError` (a `BaseException`) at the next await, so clean up and re-raise.",
)
