from lesson import *

lesson(
    id="m14-5", num="14.5", title="asyncio in practice",
    intro="The patterns every async LLM or data client needs: limiting concurrency with semaphores, client-side rate limiting, "
          "timeouts, retries with exponential backoff and jitter, worker pools on `asyncio.Queue`, deduplicating identical "
          "in-flight requests, and shutting down cleanly. All of it runs here on simulated time, so the timings in the tests are "
          "exact: a rate limiter's schedule or a timeout's effect is checked to the millisecond.",
    desc="Semaphores for rate limits, timeouts, cancellation, async LLM batches.",
    keys="asyncio semaphore bounded concurrency rate limit token bucket timeout wait_for asyncio.timeout retry exponential backoff jitter retry-after queue producer consumer worker pool task_done join shutdown single flight dedupe as_completed batch",
)

term("Semaphore", "A counter that limits how many tasks may be inside a block at once: `async with sem:` waits while the limit is reached.")
term("Backoff", "Waiting longer after each failed attempt before retrying (for example 1, 2, 4 seconds), so a struggling service gets room to recover.")
term("Jitter", "Randomness added to retry waits so that many clients that failed together do not all retry at the same instant.")

section("limits", "Bounding concurrency with a semaphore",
    p("""`gather` over 10,000 coroutines starts 10,000 requests at once, which exceeds every provider's rate limit, exhausts connection pools and memory, and gets the
    client throttled. **`asyncio.Semaphore(n)`** fixes the number of tasks allowed inside a block: `async with sem:` decrements its counter, or waits while it is
    zero, and increments it on exit. Acquire it **inside** each task, around the request itself, so that all tasks can be created at once but only `n` call the API
    at any moment (problem 3 shows the common way to get this wrong). Little's law (14.1) gives `n`: about the target requests per second times the average
    latency."""),
    ex("""
    import asyncio

    async def call(i, sem, active, peak):
        async with sem:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
            await asyncio.sleep(1.0)
            active[0] -= 1
            return i

    async def main(limit):
        sem, active, peak = asyncio.Semaphore(limit), [0], [0]
        loop = asyncio.get_running_loop()
        results = await asyncio.gather(*(call(i, sem, active, peak) for i in range(10)))
        return results == list(range(10)), peak[0], loop.time()

    print(asyncio.run(main(3)), asyncio.run(main(10)))
    """, "semaphore.py"),
    p("""With a limit of 3, ten one-second calls run in four waves and finish at 4 seconds, never more than 3 at once; with 10, all run together. Results stay in order
    because `gather` keeps argument order regardless of when each task got its turn."""),
)

section("rate", "Rate limits, timeouts and retries",
    p("""A semaphore caps **concurrency**; providers also cap **rate** (requests or tokens per minute). A client-side **token bucket** (14.2) spaces requests out: before
    each call, acquire a token, sleeping until one is available (problem 6). Combine both, and respect the server: on HTTP 429 or 503 responses, honour a
    `Retry-After` header when present."""),
    p("""Every network call needs a **timeout**: `async with asyncio.timeout(seconds):` (Python 3.11) or `await asyncio.wait_for(aw, seconds)` cancels the work and raises
    `TimeoutError` when the time is up, so one hung connection cannot stall a batch forever. Choose timeouts from measured latency percentiles (a little above the
    p99), and for streaming responses time out **between** tokens rather than over the whole stream."""),
    p("""Transient failures (timeouts, connection resets, 429, 5xx) deserve **retries with exponential backoff**: wait `base * 2 ** attempt`, capped at a maximum, and add
    **jitter**, for example a random wait between 0 and that value ("full jitter"), so that a thousand clients that failed at the same moment do not retry in
    lockstep and knock the service over again. Retry a bounded number of times, never on errors that will not change (400 bad request, 401 unauthorised, validation
    errors), and only operations that are safe to repeat (idempotent), or that carry an idempotency key."""),
)

section("queues", "Worker pools on asyncio.Queue",
    p("""For long or unbounded streams of work (items arriving from a crawler, a message queue, or a file too big to load), use a **producer-consumer** design: an
    `asyncio.Queue(maxsize=...)` between producers and a fixed number of **worker tasks**. Producers `await queue.put(item)`, which waits when the queue is full,
    giving natural **back-pressure**; each worker loops on `item = await queue.get()`, processes it, and calls `queue.task_done()`. `await queue.join()` waits until
    every item put has been marked done, after which the workers (stuck waiting on an empty queue) are cancelled. The number of workers is the concurrency limit, so
    no semaphore is needed, and memory stays bounded however much work arrives. Python 3.13 also added `queue.shutdown()` for ending consumers explicitly."""),
    ex("""
    import asyncio

    async def worker(name, queue, results):
        while True:
            item = await queue.get()
            try:
                await asyncio.sleep(item["seconds"])
                results.append((name, item["id"], asyncio.get_running_loop().time()))
            finally:
                queue.task_done()

    async def main():
        queue, results = asyncio.Queue(maxsize=2), []
        workers = [asyncio.create_task(worker(f"w{i}", queue, results)) for i in range(2)]
        for i, s in enumerate([1.0, 0.5, 0.5, 2.0, 0.5]):
            await queue.put({"id": i, "seconds": s})
        await queue.join()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        return results

    for row in asyncio.run(main()):
        print(row)
    """, "queue_workers.py"),
)

section("shutdown", "Deduplication and clean shutdown",
    p("""Two more patterns come up constantly. **Single flight**: when many tasks ask for the same thing at the same time (the same prompt, the same embedding, the same
    document), start one call and let the others await the same task, so the work is done once (problem 12). And **clean shutdown**: on cancellation or exit, stop
    accepting work, cancel or drain in-flight tasks, let their `finally` blocks and `async with` exits close connections and flush partial results, and never
    swallow `CancelledError` (14.4). Batch jobs should also write results **incrementally** (one JSONL line per finished request, keyed by request id, 12.2), so a
    crash or a cancellation loses at most the requests in flight, and a restart can skip what is done."""),
)

section("warmup", "Warm-up",
    predict("Semaphores and waves", "easy",
        code="""
        import asyncio

        async def job(i, sem, starts):
            async with sem:
                starts.append((i, asyncio.get_running_loop().time()))
                await asyncio.sleep(2 if i % 2 else 1)

        async def main(limit, n):
            sem, starts = asyncio.Semaphore(limit), []
            await asyncio.gather(*(job(i, sem, starts) for i in range(n)))
            return starts, asyncio.get_running_loop().time()

        print(asyncio.run(main(2, 5)))
        print(asyncio.run(main(1, 3))[1], asyncio.run(main(5, 5))[1])
        """,
        hints=["Even-numbered jobs take 1 second, odd ones 2. A waiting job starts as soon as any slot frees."],
        why="""With two slots, jobs 0 and 1 start at once; job 0 finishes at 1 second and job 2 takes its slot; at 2 seconds both job 1 and job 2 finish, so jobs 3 and 4 start;
        job 4 ends at 3 and job 3 at 4. A slot is reused the moment it frees, so the waves are not aligned. With one slot everything is sequential (1 + 2 + 1); with five,
        the total is the longest job."""),
    write("Gather with a concurrency limit", "easy", tag="GenAI",
        prompt="""Write `async def bounded_gather(coros, limit)` that awaits all the given coroutines with at most `limit` running at once and returns their results in order, like
        `gather`. Raise `ValueError` if `limit < 1`.""",
        code="""
        import asyncio

        async def bounded_gather(coros, limit):
            pass
        """,
        tests="""
        import asyncio
        state = {"active": 0, "peak": 0}
        async def call(i):
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            await asyncio.sleep(0.5)
            state["active"] -= 1
            return i * i
        async def main():
            loop = asyncio.get_running_loop()
            out = await bounded_gather([call(i) for i in range(7)], limit=3)
            return out, loop.time()
        out, t = asyncio.run(main())
        assert out == [i * i for i in range(7)] and state["peak"] == 3 and t == 1.5
        assert asyncio.run(bounded_gather([], 2)) == []
        try:
            asyncio.run(bounded_gather([], 0))
            assert False
        except ValueError:
            pass
        """,
        hints=["Wrap each coroutine: `async def guarded(c): async with sem: return await c`, then `gather` the wrapped ones."],
        solution="""
        import asyncio


        async def bounded_gather(coros, limit):
            if limit < 1:
                raise ValueError("limit must be at least 1")
            sem = asyncio.Semaphore(limit)

            async def guarded(coro):
                async with sem:
                    return await coro

            return await asyncio.gather(*(guarded(c) for c in coros))
        """,
        why="""The coroutine objects are created up front but do nothing until awaited, and each `guarded` wrapper awaits its coroutine only after acquiring the semaphore, so at most
        three calls are ever in progress (the grader measured the peak). Seven half-second calls in waves of three take three waves, 1.5 seconds. Order is preserved by
        `gather`. This small helper is the most reused piece of async LLM code: it turns "run all of these" into "run all of these politely"."""),
    fix("A semaphore that limits nothing", "easy", tag="GenAI",
        prompt="""`embed_all` intends to keep at most `limit` embedding calls in flight, but it acquires the semaphore around `create_task`, which returns immediately, so every call
        runs at once. Move the limiting to where the call actually happens.""",
        code="""
        import asyncio

        async def embed_all(embed, texts, limit=4):
            sem = asyncio.Semaphore(limit)
            tasks = []
            for text in texts:
                async with sem:
                    tasks.append(asyncio.create_task(embed(text)))
            return await asyncio.gather(*tasks)
        """,
        tests="""
        import asyncio
        state = {"active": 0, "peak": 0}
        async def embed(text):
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            await asyncio.sleep(1.0)
            state["active"] -= 1
            return [float(len(text))]
        out = asyncio.run(embed_all(embed, [f"doc {i}" for i in range(10)], limit=4))
        assert out == [[5.0]] * 10
        assert state["peak"] == 4
        """,
        hints=["The `async with sem:` must surround the `await embed(text)` inside the task, not the creation of the task."],
        solution="""
        import asyncio

        async def embed_all(embed, texts, limit=4):
            sem = asyncio.Semaphore(limit)

            async def one(text):
                async with sem:
                    return await embed(text)

            return await asyncio.gather(*(one(t) for t in texts))
        """,
        why="""`create_task` only schedules the coroutine and returns at once, so the semaphore was held for an instant around each scheduling and released before any embedding
        started: all ten ran together, which is exactly the burst that triggers rate-limit errors. The limit has to cover the **await of the call itself**, so it goes
        inside the coroutine each task runs. A useful habit, shown by the grader, is to measure peak concurrency in tests with a counter like this one."""),
    predict("Timeouts", "easy",
        code="""
        import asyncio

        async def slow(seconds, log):
            try:
                await asyncio.sleep(seconds)
                return "finished"
            finally:
                log.append(f"slow({seconds}) cleaned up at {asyncio.get_running_loop().time()}")

        async def main():
            log, loop = [], asyncio.get_running_loop()
            print(await asyncio.wait_for(slow(1, log), timeout=2))
            try:
                await asyncio.wait_for(slow(5, log), timeout=2)
            except TimeoutError:
                log.append(f"wait_for timed out at {loop.time()}")
            try:
                async with asyncio.timeout(1.5):
                    await slow(1, log)
                    await slow(1, log)
            except TimeoutError:
                log.append(f"block timed out at {loop.time()}")
            return log

        print(asyncio.run(main()))
        """,
        hints=["A timeout cancels the work in progress, so its `finally` runs at the moment of the timeout. `asyncio.timeout` covers the whole block."],
        why="""The first call finishes within its timeout. The second is cancelled at 2 seconds (3 seconds of loop time in total), its `finally` runs, and `wait_for` raises
        `TimeoutError`. `asyncio.timeout(1.5)` covers the whole block: the first one-second call completes, and the second is cancelled half a second in, at 4.5 seconds,
        which is why a block-level timeout is the right tool for a latency budget across several steps."""),
)

section("medium", "Medium",
    write("Retries with exponential backoff and jitter", "medium", tag="GenAI",
        prompt="""Write `async def call_with_retry(fn, attempts=4, base=0.5, cap=8.0, rng=random.random)`. It awaits `fn()`; on `TransientError` it sleeps and retries, up to `attempts`
        calls in total, then re-raises. The wait before retry `k` (0-based) is `rng() * min(cap, base * 2 ** k)` ("full jitter"), unless the error has a `retry_after`
        attribute that is not `None`, in which case it waits exactly that many seconds. Other exceptions propagate at once.""",
        code="""
        import asyncio, random

        class TransientError(Exception):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after

        async def call_with_retry(fn, attempts=4, base=0.5, cap=8.0, rng=random.random):
            pass
        """,
        tests="""
        import asyncio
        def scripted(*outcomes):
            it = iter(outcomes)
            calls = []
            async def fn():
                calls.append(asyncio.get_running_loop().time())
                o = next(it)
                if isinstance(o, BaseException):
                    raise o
                return o
            return fn, calls
        fn, calls = scripted(TransientError("429"), TransientError("503"), "ok")
        assert asyncio.run(call_with_retry(fn, rng=lambda: 1.0)) == "ok" and calls == [0.0, 0.5, 1.5]
        fn, calls = scripted(TransientError("429", retry_after=3.0), "ok")
        assert asyncio.run(call_with_retry(fn, rng=lambda: 0.5)) == "ok" and calls == [0.0, 3.0]
        fn, calls = scripted(*[TransientError("down")] * 4)
        try:
            asyncio.run(call_with_retry(fn, attempts=4, base=4.0, cap=8.0, rng=lambda: 0.5))
            assert False
        except TransientError:
            pass
        assert calls == [0.0, 2.0, 6.0, 10.0]
        fn, calls = scripted(ValueError("bad request"))
        try:
            asyncio.run(call_with_retry(fn))
            assert False
        except ValueError:
            assert calls == [0.0]
        """,
        hints=["Loop `for k in range(attempts)`; in `except TransientError as e`, re-raise if `k == attempts - 1`, else compute the delay and `await asyncio.sleep(delay)`."],
        solution="""
        import asyncio, random


        class TransientError(Exception):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after


        async def call_with_retry(fn, attempts=4, base=0.5, cap=8.0, rng=random.random):
            for k in range(attempts):
                try:
                    return await fn()
                except TransientError as e:
                    if k == attempts - 1:
                        raise
                    if e.retry_after is not None:
                        delay = e.retry_after
                    else:
                        delay = rng() * min(cap, base * 2 ** k)
                    await asyncio.sleep(delay)
        """,
        why="""The exponential part doubles the ceiling of each wait (0.5, 1, 2, 4 seconds, up to `cap`), giving a failing service more room each time, and the jitter draws the
        actual wait uniformly below that ceiling, so a crowd of clients that failed together spreads out instead of retrying in synchronised waves (the "thundering
        herd"). A server's `Retry-After` overrides the formula because the server knows when it will have capacity. Injecting `rng` makes the schedule exact in tests:
        with `rng() == 1` the calls happen at 0, 0.5 and 1.5 seconds. Non-transient errors fail fast, since retrying a bad request only burns quota."""),
    write("An async token-bucket rate limiter", "medium", tag="GenAI",
        prompt="""Write `AsyncRateLimiter(rate, capacity)` with `async def acquire(self)` that waits until a token is available and takes it. The bucket starts full and refills at `rate`
        tokens per second (up to `capacity`), measured with the running loop's clock. Concurrent callers must be served in arrival order and never exceed the rate: hold an
        `asyncio.Lock` while computing the wait and sleeping.""",
        code="""
        import asyncio

        class AsyncRateLimiter:
            pass
        """,
        tests="""
        import asyncio
        async def main():
            limiter = AsyncRateLimiter(rate=2.0, capacity=3)
            loop = asyncio.get_running_loop()
            starts = []
            async def request(i):
                await limiter.acquire()
                starts.append((i, loop.time()))
            await asyncio.gather(*(request(i) for i in range(7)))
            await asyncio.sleep(10)
            await request(7)
            return starts
        starts = asyncio.run(main())
        assert starts[:7] == [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.5), (4, 1.0), (5, 1.5), (6, 2.0)]
        assert starts[7] == (7, 12.0)
        """,
        hints=["Track `tokens` and `last`; refill with `(now - last) * rate`, capped at `capacity`.",
               "Inside `async with self._lock:`, if fewer than one token, `await asyncio.sleep((1 - tokens) / rate)` then refill again; take one token."],
        solution="""
        import asyncio


        class AsyncRateLimiter:
            def __init__(self, rate, capacity):
                self.rate, self.capacity = rate, capacity
                self.tokens = float(capacity)
                self.last = None
                self._lock = asyncio.Lock()

            def _refill(self):
                now = asyncio.get_running_loop().time()
                if self.last is not None:
                    self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
                self.last = now

            async def acquire(self):
                async with self._lock:
                    self._refill()
                    if self.tokens < 1:
                        await asyncio.sleep((1 - self.tokens) / self.rate)
                        self._refill()
                    self.tokens -= 1
        """,
        why="""The bucket allows a burst of `capacity` requests at once, then one every `1 / rate` seconds, which is how most provider limits behave; the schedule in the test
        (three at once, then every half second) is exactly that. Holding the lock while sleeping makes waiting callers queue up in arrival order (an `asyncio.Lock`
        is fair: waiters acquire it first come, first served), so no two callers can compute a wait from the same token count and both go through. After ten idle
        seconds the bucket is full again, so request 7 does not wait. The clock is read from the loop, so the limiter works unchanged on this site's simulated time
        and in production."""),
    fix("One hung call stalls the whole batch", "medium", tag="GenAI",
        prompt="""`ask_all` runs all questions concurrently, but a single call that never returns (a stuck connection) keeps the batch waiting forever. Add a per-call timeout of
        `timeout` seconds using `asyncio.timeout`, recording `"timeout"` for calls that exceed it, and keep the other answers.""",
        code="""
        import asyncio

        async def ask_all(ask, questions, timeout=5.0):
            return await asyncio.gather(*(ask(q) for q in questions))
        """,
        tests="""
        import asyncio
        async def ask(q):
            await asyncio.sleep(10_000 if "stuck" in q else 1.0)
            return q.upper()
        async def main():
            loop = asyncio.get_running_loop()
            out = await ask_all(ask, ["refund?", "stuck call", "shipping?"], timeout=3.0)
            return out, loop.time()
        out, t = asyncio.run(main())
        assert out == ["REFUND?", "timeout", "SHIPPING?"]
        assert t == 3.0
        """,
        hints=["Wrap each call: `async def one(q): try: async with asyncio.timeout(timeout): return await ask(q) except TimeoutError: return \"timeout\"`."],
        solution="""
        import asyncio

        async def ask_all(ask, questions, timeout=5.0):
            async def one(q):
                try:
                    async with asyncio.timeout(timeout):
                        return await ask(q)
                except TimeoutError:
                    return "timeout"

            return await asyncio.gather(*(one(q) for q in questions))
        """,
        why="""Without a timeout, `gather` waits for its slowest member, and a request with no timeout can be slow forever: the batch here would have finished after 10,000 seconds.
        A per-call timeout cancels just the stuck call at 3 seconds and turns it into a recorded outcome, so the batch completes at the deadline with every other answer.
        Timeouts belong on every network call in production, at the client level (connect and read timeouts) and around the logical operation, as here."""),
    trace("Producers, consumers and join", "medium",
        prompt="Fill in `log` after each marked line. One producer puts three items; one consumer takes 1 second per item.",
        code="""
        import asyncio

        async def scenario(maxsize):
            q, log = asyncio.Queue(maxsize=maxsize), []
            loop = asyncio.get_running_loop()

            async def consumer():
                while True:
                    item = await q.get()
                    await asyncio.sleep(1.0)
                    log.append(f"done {item} @{loop.time():g}")
                    q.task_done()

            c = asyncio.create_task(consumer())
            for item in "abc":
                await q.put(item)
                log.append(f"put {item} @{loop.time():g}")
            await q.join()
            log.append(f"joined @{loop.time():g}")
            c.cancel()
            return log

        log = asyncio.run(scenario(0))  # row: "unbounded queue"
        log = asyncio.run(scenario(1))  # row: "maxsize=1 back-pressure"
        """,
        trace_vars=["log"],
        hints=["`maxsize=0` means unbounded: `put` never waits. With `maxsize=1`, `put` waits while an item is in the queue.",
               "The consumer only takes an item out of the queue when it calls `get`."],
        why="""With an unbounded queue, the producer puts all three items at time 0 without waiting, and `join` waits until the consumer has marked each done, at 3 seconds. With
        `maxsize=1`, the queue holds one item: `a` is taken by the consumer at once, `b` fills the queue, and `put c` must wait until the consumer takes `b` after finishing
        `a` at 1 second. That waiting is **back-pressure**: a fast producer is slowed to the consumers' pace, so memory stays bounded. The total time is the same,
        because the consumer was the bottleneck either way."""),
    write("A worker pool on a queue", "medium", tag="Data work",
        prompt="""Write `async def process_all(items, handle, workers=3, maxsize=10)` that starts `workers` worker tasks reading from an `asyncio.Queue(maxsize)`, puts every item (with
        its index) on the queue, waits for `queue.join()`, cancels the workers, and returns a list of results in input order. A handler error is stored as `f"error:
        {ExceptionName}"` for that item; it must not kill the worker.""",
        code="""
        import asyncio

        async def process_all(items, handle, workers=3, maxsize=10):
            pass
        """,
        tests="""
        import asyncio
        state = {"active": 0, "peak": 0}
        async def handle(x):
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            try:
                await asyncio.sleep(1.0)
                if x < 0:
                    raise ValueError("negative")
                return x * 10
            finally:
                state["active"] -= 1
        async def main():
            loop = asyncio.get_running_loop()
            out = await process_all([1, 2, -3, 4, 5, 6, 7], handle, workers=3, maxsize=2)
            return out, loop.time()
        out, t = asyncio.run(main())
        assert out == [10, 20, "error: ValueError", 40, 50, 60, 70] and state["peak"] == 3 and t == 3.0
        assert asyncio.run(process_all([], handle)) == []
        """,
        hints=["Each worker loops: `i, item = await queue.get()`, then `try: results[i] = await handle(item) except Exception as e: ...`, and `queue.task_done()` in a `finally`.",
               "After `await queue.join()`, cancel the workers and `await asyncio.gather(*workers, return_exceptions=True)`."],
        solution="""
        import asyncio


        async def process_all(items, handle, workers=3, maxsize=10):
            queue = asyncio.Queue(maxsize=maxsize)
            results = [None] * len(items)

            async def worker():
                while True:
                    i, item = await queue.get()
                    try:
                        results[i] = await handle(item)
                    except Exception as e:
                        results[i] = f"error: {type(e).__name__}"
                    finally:
                        queue.task_done()

            tasks = [asyncio.create_task(worker()) for _ in range(workers)]
            try:
                for pair in enumerate(items):
                    await queue.put(pair)
                await queue.join()
            finally:
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            return results
        """,
        why="""The number of workers is the concurrency limit (the peak was exactly 3), and the bounded queue makes the producer wait instead of loading every item into memory,
        which matters when items come from a large file or a crawler. Each item carries its index, so results land in input order whatever the completion order.
        `task_done` sits in a `finally`, so a failing item still counts as processed, otherwise `join` would wait forever. After `join`, the workers are idle on `get` and
        are cancelled and awaited, in a `finally` so they are cleaned up even if putting items fails. Seven one-second items on three workers take three rounds, 3 seconds."""),
    predict("Completion order with asyncio.as_completed", "medium",
        code="""
        import asyncio

        async def retrieve(source, seconds):
            await asyncio.sleep(seconds)
            return source

        async def main():
            loop = asyncio.get_running_loop()
            jobs = [retrieve("wiki", 1.2), retrieve("faq", 0.3), retrieve("tickets", 0.8)]
            order = []
            for next_done in asyncio.as_completed(jobs):
                source = await next_done
                order.append((source, loop.time()))
            first = await asyncio.gather(retrieve("a", 2), retrieve("b", 1))
            return order, first, loop.time()

        print(asyncio.run(main()))
        """,
        hints=["`as_completed` yields awaitables in the order they finish; `gather` returns in argument order."],
        why="""`asyncio.as_completed` hands back results as soon as each finishes, fastest first, which lets a RAG service start building an answer from the quickest source or show
        progress in a batch job. `gather` waits for all and returns results in argument order, so `a` comes first even though `b` finished earlier. Loop times are
        cumulative: the `as_completed` loop ends at 1.2 seconds and the `gather` adds 2 more."""),
)

section("hard", "Hard",
    write("A resilient async batch runner", "hard", tag="GenAI",
        prompt="""Write `async def run_batch(requests, call, limit=4, timeout=10.0, attempts=3, done_ids=())` for a list of `{"id": ..., "prompt": ...}` requests. Skip requests whose id is
        in `done_ids` (already processed in an earlier run). Run the rest with at most `limit` concurrent calls; each attempt has a timeout; retry up to `attempts` calls in
        total on `TimeoutError` or `ConnectionError`, with no wait between attempts. Append each finished request, **in completion order**, to the returned `records` list as
        `{"id": ..., "ok": bool, "output": ... or None, "error": None or "ExceptionName", "attempts": n}`, and return `{"records": records, "skipped": [ids]}`.""",
        code="""
        import asyncio

        async def run_batch(requests, call, limit=4, timeout=10.0, attempts=3, done_ids=()):
            pass
        """,
        tests="""
        import asyncio
        tries = {}
        state = {"active": 0, "peak": 0}
        async def call(prompt):
            tries[prompt] = tries.get(prompt, 0) + 1
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            try:
                if prompt == "hangs once" and tries[prompt] == 1:
                    await asyncio.sleep(100)
                if prompt == "always down":
                    raise ConnectionError("refused")
                if prompt == "bad":
                    raise ValueError("invalid prompt")
                await asyncio.sleep(len(prompt) / 10)
                return prompt.upper()
            finally:
                state["active"] -= 1
        reqs = [{"id": f"r{i}", "prompt": p} for i, p in enumerate(["short", "hangs once", "always down", "bad", "a longer prompt", "done before"])]
        async def main():
            loop = asyncio.get_running_loop()
            out = await run_batch(reqs, call, limit=2, timeout=2.0, attempts=3, done_ids={"r5"})
            return out, loop.time()
        out, t = asyncio.run(main())
        recs = {r["id"]: r for r in out["records"]}
        assert out["skipped"] == ["r5"] and len(out["records"]) == 5
        assert recs["r0"] == {"id": "r0", "ok": True, "output": "SHORT", "error": None, "attempts": 1}
        assert recs["r1"] == {"id": "r1", "ok": True, "output": "HANGS ONCE", "error": None, "attempts": 2}
        assert recs["r2"] == {"id": "r2", "ok": False, "output": None, "error": "ConnectionError", "attempts": 3}
        assert recs["r3"] == {"id": "r3", "ok": False, "output": None, "error": "ValueError", "attempts": 1}
        assert [r["id"] for r in out["records"]] == ["r0", "r2", "r3", "r4", "r1"] and state["peak"] == 2 and t == 3.0
        """,
        hints=["One coroutine per request: inside `async with sem:`, loop over attempts with `async with asyncio.timeout(timeout):` around `await call(prompt)`.",
               "Append the record to `records` when the request finishes; `gather` all the per-request coroutines."],
        solution="""
        import asyncio


        async def run_batch(requests, call, limit=4, timeout=10.0, attempts=3, done_ids=()):
            done_ids = set(done_ids)
            sem = asyncio.Semaphore(limit)
            records, skipped = [], []

            async def one(req):
                async with sem:
                    error = None
                    for attempt in range(1, attempts + 1):
                        try:
                            async with asyncio.timeout(timeout):
                                output = await call(req["prompt"])
                            records.append({"id": req["id"], "ok": True, "output": output, "error": None, "attempts": attempt})
                            return
                        except (TimeoutError, ConnectionError) as e:
                            error = e
                        except Exception as e:
                            records.append({"id": req["id"], "ok": False, "output": None, "error": type(e).__name__, "attempts": attempt})
                            return
                    records.append({"id": req["id"], "ok": False, "output": None, "error": type(error).__name__, "attempts": attempts})

            todo = []
            for req in requests:
                if req["id"] in done_ids:
                    skipped.append(req["id"])
                else:
                    todo.append(req)
            await asyncio.gather(*(one(r) for r in todo))
            return {"records": records, "skipped": skipped}
        """,
        why="""This is the skeleton of every production batch client, and each feature answers a real failure. The semaphore keeps concurrency at the limit (peak 2). The per-attempt
        timeout turns the hung first call into a retry after 2 seconds instead of a stalled batch. Retries cover transient errors only; the invalid prompt fails at once.
        Records are appended as requests finish, in completion order, which is what you write to a JSONL file one line at a time (12.2), so a crash loses only the
        requests in flight, and `done_ids` lets the next run skip everything already recorded. Holding the semaphore across retries keeps the retrying request's slot;
        releasing it between attempts (with a backoff sleep outside the semaphore) is a reasonable alternative when retries are slow."""),
    write("Single-flight deduplication", "hard", tag="GenAI",
        prompt="""Write `SingleFlight` with `async def run(self, key, fn)`: if a call for `key` is already in progress, await its result instead of starting another; otherwise start
        `fn()` as a task, store it, and remove it when it finishes (success or failure) so a later call starts fresh. All waiters receive the same result or the same
        exception. Add `self.started`, counting calls actually made per key.""",
        code="""
        import asyncio

        class SingleFlight:
            pass
        """,
        tests="""
        import asyncio
        sf = SingleFlight()
        calls = []
        def embed(text, fail=False):
            async def fn():
                calls.append(text)
                await asyncio.sleep(1.0)
                if fail:
                    raise ConnectionError("embedding service down")
                return [float(len(text))]
            return fn
        async def main():
            loop = asyncio.get_running_loop()
            same = await asyncio.gather(*(sf.run("refund", embed("refund")) for _ in range(5)), sf.run("ship", embed("shipping")))
            t1 = loop.time()
            again = await sf.run("refund", embed("refund"))
            results = await asyncio.gather(sf.run("x", embed("x", fail=True)), sf.run("x", embed("x")), return_exceptions=True)
            return same, t1, again, results
        same, t1, again, results = asyncio.run(main())
        assert same == [[6.0]] * 5 + [[8.0]] and t1 == 1.0 and again == [6.0]
        assert calls == ["refund", "shipping", "refund", "x"] and sf.started == {"refund": 2, "ship": 1, "x": 1}
        assert all(isinstance(r, ConnectionError) for r in results) and sf._inflight == {}
        """,
        hints=["Keep `self._inflight = {}` mapping key to task. If the key is present, `return await self._inflight[key]`.",
               "Otherwise create the task, store it, and remove it with `task.add_done_callback(lambda t: self._inflight.pop(key, None))`, then await it."],
        solution="""
        import asyncio


        class SingleFlight:
            def __init__(self):
                self._inflight = {}
                self.started = {}

            async def run(self, key, fn):
                task = self._inflight.get(key)
                if task is None:
                    self.started[key] = self.started.get(key, 0) + 1
                    task = asyncio.create_task(fn())
                    self._inflight[key] = task
                    task.add_done_callback(lambda t, k=key: self._inflight.pop(k, None))
                return await task
        """,
        why="""When five users ask the same question at once, or a batch contains duplicate texts, a cache cannot help because the first answer is not there yet; single flight
        shares the **in-progress** task, so the expensive call runs once and every waiter awaits the same task, receiving the same value or the same exception. The done
        callback removes the entry when the task finishes, so failures are not cached forever and a later request starts fresh (the third `refund` call ran again).
        Because the event loop runs one task at a time, the check-and-insert in `run` needs no lock: there is no `await` between them (14.4). Combined with a result cache
        (13.3's TTL cache), this removes most duplicate LLM and embedding calls."""),
    fix("Read the code: an async ingestion service", "hard", tag="RAG",
        prompt="""`ingest` embeds documents for a vector store. In production it overwhelms the embedding API (no concurrency limit), hangs forever when one request stalls (no
        timeout), and cannot be stopped: its broad `except BaseException` swallows `CancelledError`, so cancelling the job just moves on to the next document. Fix it:
        limit concurrency to `limit` with a semaphore, apply a per-document timeout recording `"timeout"`, record other `Exception`s as `"error: Name"`, and let
        cancellation propagate.""",
        code="""
        import asyncio


        async def ingest(docs, embed, store, limit=4, timeout=5.0):
            async def one(doc):
                try:
                    vector = await embed(doc["text"])
                    store[doc["id"]] = vector
                    return "ok"
                except BaseException as e:
                    return f"error: {type(e).__name__}"

            return await asyncio.gather(*(one(d) for d in docs))
        """,
        tests="""
        import asyncio
        state = {"active": 0, "peak": 0}
        async def embed(text):
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            try:
                await asyncio.sleep(1000 if text == "stall" else 1.0)
                if text == "bad":
                    raise ValueError("unsupported")
                return [float(len(text))]
            finally:
                state["active"] -= 1
        docs = [{"id": f"d{i}", "text": t} for i, t in enumerate(["refunds", "stall", "bad", "shipping", "returns", "warranty"])]
        async def main():
            store = {}
            loop = asyncio.get_running_loop()
            out = await ingest(docs, embed, store, limit=2, timeout=3.0)
            return out, store, loop.time()
        out, store, t = asyncio.run(main())
        assert out == ["ok", "timeout", "error: ValueError", "ok", "ok", "ok"] and sorted(store) == ["d0", "d3", "d4", "d5"]
        assert state["peak"] == 2 and t == 4.0
        async def cancel_midway():
            task = asyncio.create_task(ingest([{"id": str(i), "text": "x" * 5} for i in range(10)], embed, {}, limit=2))
            await asyncio.sleep(1.5)
            task.cancel()
            try:
                await task
                return "not cancelled"
            except asyncio.CancelledError:
                return "cancelled", asyncio.get_running_loop().time()
        assert asyncio.run(cancel_midway()) == ("cancelled", 1.5)
        """,
        hints=["Inside `one`, `async with sem:` then `async with asyncio.timeout(timeout):` around the embed call.",
               "Catch `TimeoutError` first, then `Exception`; never `BaseException`, so `CancelledError` propagates."],
        solution="""
        import asyncio


        async def ingest(docs, embed, store, limit=4, timeout=5.0):
            sem = asyncio.Semaphore(limit)

            async def one(doc):
                async with sem:
                    try:
                        async with asyncio.timeout(timeout):
                            vector = await embed(doc["text"])
                    except TimeoutError:
                        return "timeout"
                    except Exception as e:
                        return f"error: {type(e).__name__}"
                    store[doc["id"]] = vector
                    return "ok"

            return await asyncio.gather(*(one(d) for d in docs))
        """,
        why="""Three production failures, three fixes. The semaphore keeps the embedding API at 2 concurrent calls instead of all at once. The per-document timeout turns the stalled
        request into a `"timeout"` record after 3 seconds, and the batch finishes at 4 seconds instead of 1,000. Most importantly, `except BaseException` caught the
        `CancelledError` that `task.cancel()` raises inside each awaiting coroutine, so every cancelled document just returned an error string and the job carried on;
        catching `Exception` lets cancellation propagate, `gather` is cancelled, and the job stops at once (at 1.5 seconds in the test). Storing the vector only after
        a successful call keeps the store free of partial results."""),
    predict("Shutting down workers", "hard",
        code="""
        import asyncio

        log = []

        async def worker(name, delay):
            try:
                while True:
                    await asyncio.sleep(delay)
                    log.append(f"{name} tick")
            except asyncio.CancelledError:
                log.append(f"{name} flushing")
                raise
            finally:
                log.append(f"{name} closed")

        async def main():
            tasks = [asyncio.create_task(worker("a", 1.0)), asyncio.create_task(worker("b", 1.5))]
            await asyncio.sleep(3.2)
            for t in tasks:
                t.cancel()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [type(r).__name__ for r in results], [t.cancelled() for t in tasks], asyncio.get_running_loop().time()

        print(asyncio.run(main()), log)
        """,
        hints=["Each worker ticks on its own timer. `cancel()` raises `CancelledError` at the next await; `gather(..., return_exceptions=True)` collects it."],
        why="""Worker `a` ticks at 1, 2 and 3 seconds and `b` at 1.5 and 3, so by 3.2 seconds there are five ticks. Cancelling raises `CancelledError` inside each worker at its sleep;
        the handler runs (the place to flush buffered results) and re-raises, then `finally` closes resources. `gather` with `return_exceptions=True` waits for both to
        finish cancelling and returns the `CancelledError` instances instead of raising, so a shutdown routine can wait for every worker to clean up before the program
        exits."""),
)

section("interview", "Interview questions",
    explain("How would you call an LLM API 100,000 times as fast as the limits allow, and reliably?", "medium", tag="Interview",
        why="""Use an async client with **bounded concurrency** (a semaphore or a fixed pool of queue workers) sized by Little's law from the provider's limits and observed latency, plus a
        client-side **rate limiter** (token bucket) for requests and estimated tokens per minute. Give every call a **timeout**, and retry transient failures (timeouts, connection
        errors, 429, 5xx) with **exponential backoff and jitter**, honouring `Retry-After`, a bounded number of times; fail fast on 4xx errors. Stream inputs from a file or
        queue instead of loading everything, and write each result **as it completes** to durable storage (JSONL keyed by request id), so the job is **resumable** and
        never pays twice for a request. Track progress, error rates, latency percentiles and token cost as it runs, and stop or slow down automatically if error rates
        spike. Deduplicate identical prompts (cache and single flight). For offline work, consider the provider's **batch API**, which trades latency (hours) for
        lower cost and separate limits."""),
    explain("Why add jitter to exponential backoff?", "medium", tag="Interview",
        why="""When a service fails briefly, many clients fail at the same moment. With plain exponential backoff, they all wait 1, 2, 4 seconds exactly and retry in synchronised waves,
        so each wave hits the recovering service with the full load at once and can knock it down again (the "thundering herd"). Jitter randomises each client's wait, for
        example uniformly between 0 and the exponential ceiling ("full jitter"), which spreads retries over the interval and turns spikes into a smooth, lower load, at the
        cost of slightly less predictable individual delays. It also avoids retries colliding with periodic jobs. Combined with a cap on the wait, a maximum number of
        attempts, and honouring `Retry-After`, it is the standard retry policy recommended by cloud providers and implemented by libraries such as `tenacity` and
        `backoff`."""),
    explain("How do you shut down an asyncio service gracefully?", "hard", tag="Interview",
        why="""Stop taking new work first: stop accepting connections or reading from the input queue, and signal producers (an `Event`, `queue.shutdown()` in 3.13+). Then let
        in-flight work finish within a grace period (`asyncio.wait` with a timeout, or `queue.join()`), and cancel what remains; cancellation raises `CancelledError` at each
        task's current await, so tasks run their `finally` blocks and `async with` exits, flushing buffers, committing or rolling back, and closing clients. Await the
        cancelled tasks (`gather(..., return_exceptions=True)`) so cleanup actually completes before closing shared resources such as HTTP clients and database pools, in
        reverse order of creation. Never swallow `CancelledError`, and shield the few steps that must finish (writing a checkpoint) with `asyncio.shield`. Handle
        SIGTERM by triggering this sequence (`loop.add_signal_handler` on Unix), because container platforms send it before killing the process; frameworks such as
        FastAPI expose this as lifespan shutdown hooks. Structured concurrency with `TaskGroup` makes most of this automatic, since cancelling the group cancels its
        children."""),
)

recap(
    "Bound concurrency with a semaphore acquired inside each task, around the call; measure peak concurrency in tests.",
    "Respect rate limits with a token bucket, give every call a timeout (`asyncio.timeout`), and retry transient errors with capped exponential backoff, jitter and `Retry-After`.",
    "For streams of work, use worker tasks on a bounded `asyncio.Queue` (back-pressure), `task_done` in `finally`, `join`, then cancel the workers.",
    "Deduplicate in-flight work with single flight; write results incrementally so batches are resumable.",
    "Shut down by stopping intake, draining or cancelling tasks, awaiting their cleanup, and never swallowing `CancelledError`.",
)
