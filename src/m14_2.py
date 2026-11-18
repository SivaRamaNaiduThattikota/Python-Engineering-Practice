from lesson import *
from diagrams import *

lesson(
    id="m14-2", num="14.2", title="Threads and futures",
    intro="Threads are the simplest way to overlap I/O in Python: calls to model APIs, downloads, database queries. `threading` "
          "briefly, then `concurrent.futures`, which is what you should use: executors, futures, `submit`, `map` and "
          "`as_completed`, error handling, keeping results out of shared state, locks for the state you must share, and how many "
          "threads to use. On this site executors run each task immediately and in order (14.1), so problems check correctness; "
          "run them locally for real overlap.",
    desc="`threading` and `concurrent.futures` for I/O-bound work.",
    keys="threading thread start join daemon excepthook concurrent.futures threadpoolexecutor executor future submit result exception done add_done_callback cancel map as_completed wait first_exception lock rlock queue thread-safe max_workers io-bound",
)

term("Thread", "An independent sequence of execution inside a process, sharing the process's memory with other threads.")
term("Executor", "An object that runs submitted functions on a pool of workers (threads or processes) and hands back futures.")
term("Future", "A placeholder for the result of a call that may not have finished; it later holds either a return value or an exception.")

section("threading", "`threading.Thread` in brief",
    p("""A `threading.Thread(target=fn, args=(...))` runs `fn` in a new thread once you call `start()`; `join()` waits for it to finish. The calling code continues
    immediately after `start()`, which is the point: while one thread waits for a network reply, others run. Raw threads have two awkward properties. They
    **return nothing**: a target's return value is discarded, so results must be passed back through shared structures. And an exception in a thread does
    **not** reach the code that started it: it is printed by `threading.excepthook` and the thread ends, while `join()` returns normally (problem 10).
    `daemon=True` threads are killed abruptly when the program exits, which suits background helpers but loses work in progress."""),
    p("""For almost all application code, use **`concurrent.futures`** instead: it manages a pool of threads, passes return values and exceptions back, and fits in
    a `with` block. Reach for raw threads only for long-lived background workers (a log shipper, a heartbeat), usually communicating through a
    `queue.Queue`."""),
)

section("executors", "Executors and futures",
    fig(chain(["pool.submit(fn, x)", "returns a Future|at once", "a worker thread|runs fn(x)", ("future.result()|waits, or re-raises", "good")]),
        "An executor hands work to a pool and gives back a future: a placeholder for the result, or for the exception."),
    p("""**`ThreadPoolExecutor(max_workers=n)`** keeps `n` worker threads. `executor.submit(fn, *args, **kwargs)` schedules one call and immediately returns a
    **`Future`**. `future.result(timeout=None)` waits for the call and returns its value, or **re-raises its exception** in the calling thread, with the
    original traceback; `future.exception()` returns the exception instead of raising, `future.done()` tells whether it finished, `future.cancel()` cancels a
    call that has not started, and `add_done_callback(fn)` runs `fn(future)` when it finishes. Using the executor in a `with` block calls `shutdown(wait=True)` at
    the end, so the block does not exit until every submitted call is done, and no new work can be submitted afterwards."""),
    p("""Two ways to collect results. **`executor.map(fn, items)`** returns an iterator of results **in input order**, like the built-in `map`, and if a call
    raised, iterating re-raises that exception when its turn comes, so results after it are lost unless you handle errors inside `fn`. **`as_completed(futures)`**
    yields futures **as they finish**, fastest first, which lets you process or report results early, show progress, and handle each error separately; keep a
    dict from future to input to know which input each result belongs to. `concurrent.futures.wait(futures, return_when=FIRST_EXCEPTION)` waits until the first
    failure, for fail-fast batches."""),
    ex("""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def classify(text):
        if not text:
            raise ValueError("empty message")
        return "spam" if "prize" in text.lower() else "ham"

    messages = ["Win a PRIZE", "Lunch?", "", "Prize draw today"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(classify, m): i for i, m in enumerate(messages)}
        results = [None] * len(messages)
        for future in as_completed(futures):
            i = futures[future]
            error = future.exception()
            results[i] = f"error: {error}" if error else future.result()
    print(results)

    with ThreadPoolExecutor(max_workers=4) as pool:
        it = pool.map(classify, messages)
        print(next(it), next(it))
        try:
            next(it)
        except ValueError as e:
            print("map raised:", e)
    """, "futures.py"),
    p("""The dict from future to index puts every result back in its place whatever the completion order, and each failure is recorded rather than aborting the
    batch. With `map`, the first two results arrive normally, and the third raises when iterated."""),
)

section("state", "Results instead of shared state",
    p("""The safest concurrent code shares nothing mutable: each task receives its inputs, returns its result, and the caller combines results after collecting them.
    Then there is nothing to race on. When tasks must update shared state, protect it with **`threading.Lock`**: `with lock:` around every read-modify-write of
    that state, kept as short as possible (never around a network call, or the threads queue behind the lock and you are back to sequential). `RLock` can be
    re-acquired by the thread that holds it. `queue.Queue` is a thread-safe FIFO for producer and consumer threads, with blocking `put` and `get`. Individual
    operations on built-in containers, such as `list.append`, happen to be safe in CPython, but compound ones (`if key not in d: d[key] = ...`, `counter += 1`)
    are not, and code should not rely on implementation details, especially with free-threaded Python arriving."""),
    p("""Clients deserve a note: most HTTP and LLM SDK clients (`httpx.Client`, `requests.Session`, the OpenAI and Anthropic clients) are designed to be shared across
    threads and reuse connections; create one and pass it to the tasks rather than one per call. Check each library's documentation, because some objects (such
    as database connections or SQLite cursors) must not be shared."""),
)

section("sizing", "How many threads",
    p("""For I/O-bound work, the right number of threads is set by what you are waiting on, not by CPU cores: Little's law (14.1) gives the concurrency needed for a target
    throughput, and the provider's rate limits and the remote service's capacity cap it. The default `max_workers` is `min(32, os.cpu_count() + 4)`, a reasonable
    start for mixed workloads. Too many threads waste memory (each has its own stack), increase contention, and can overload the service you call; for thousands
    of concurrent requests, asyncio (14.4) scales better. Always set **timeouts** on network calls made from threads: a thread stuck on a request without a timeout
    is a worker lost for good."""),
)

section("warmup", "Warm-up",
    predict("Futures from submit and map", "easy",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def parse(x):
            return int(x)

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(parse, "42")
            f2 = pool.submit(parse, "forty")
            print(f1.result(), type(f2.exception()).__name__, f2.done())
            try:
                f2.result()
            except ValueError as e:
                print("re-raised:", e)
            print(list(pool.map(parse, ["1", "2", "3"])), list(pool.map(lambda a, b: a * b, [1, 2, 3], [10, 20, 30])))
        try:
            pool.submit(parse, "7")
        except RuntimeError as e:
            print("RuntimeError:", e)
        """,
        hints=["`result()` re-raises the call's exception; `exception()` returns it. `map` with several iterables passes one item from each. A shut-down executor refuses new work."],
        why="""A future holds either a value or an exception: `result()` returns the value or raises the stored exception in the calling thread, and `exception()` hands the
        exception back for inspection. `map` returns results in input order, and with several iterables it zips them like the built-in. After the `with` block the
        executor is shut down, so `submit` raises `RuntimeError`, which catches code that accidentally schedules work after the batch."""),
    write("Fetch many URLs, keeping errors", "easy", tag="GenAI",
        prompt="""Write `fetch_all(fetch, urls, max_workers=8)` that calls `fetch(url)` for every URL on a `ThreadPoolExecutor` and returns a dict mapping each URL, **in input
        order**, to either the result or the string `f"error: {ExceptionName}: {message}"`. Duplicate URLs are fetched once.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def fetch_all(fetch, urls, max_workers=8):
            pass
        """,
        tests="""
        calls = []
        def fetch(url):
            calls.append(url)
            if "bad" in url:
                raise ConnectionError("reset by peer")
            return f"<html>{url}</html>"
        urls = ["https://a.io/1", "https://bad.io", "https://a.io/2", "https://a.io/1"]
        out = fetch_all(fetch, urls, max_workers=3)
        assert list(out) == ["https://a.io/1", "https://bad.io", "https://a.io/2"]
        assert out["https://bad.io"] == "error: ConnectionError: reset by peer" and out["https://a.io/2"] == "<html>https://a.io/2</html>"
        assert sorted(calls) == sorted(set(urls)) and fetch_all(fetch, []) == {}
        """,
        hints=["`unique = list(dict.fromkeys(urls))` removes duplicates and keeps order.",
               "Map each future to its URL, collect with `as_completed`, then build the result dict in `unique` order."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor, as_completed


        def fetch_all(fetch, urls, max_workers=8):
            unique = list(dict.fromkeys(urls))
            results = {}
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(fetch, url): url for url in unique}
                for future in as_completed(futures):
                    url = futures[future]
                    error = future.exception()
                    results[url] = f"error: {type(error).__name__}: {error}" if error else future.result()
            return {url: results[url] for url in unique}
        """,
        why="""Each URL becomes one future, and the dict from future to URL tells the collector which result is which, whatever the completion order; rebuilding the output in
        input order makes the function's result deterministic even though threads finish in any order. Using `exception()` turns each failure into data instead
        of aborting the batch, which is what a crawler or an evaluation run needs. Deduplicating first avoids paying twice for the same call."""),
    fix("Errors that vanish with the futures", "easy", tag="Data work",
        prompt="""`process_all(fn, items)` submits every item but never looks at the futures, so it returns nothing and failures go unnoticed. Make it return the results in
        input order, and if any call failed, raise `RuntimeError(f"{n} of {total} items failed")` chained from the **first** failure (in input order) after all calls
        have finished.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def process_all(fn, items, max_workers=4):
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for item in items:
                    pool.submit(fn, item)
        """,
        tests="""
        assert process_all(lambda x: x * 2, [1, 2, 3]) == [2, 4, 6]
        def risky(x):
            if x % 2:
                raise ValueError(f"odd {x}")
            return x
        try:
            process_all(risky, [2, 3, 4, 5])
            assert False
        except RuntimeError as e:
            assert str(e) == "2 of 4 items failed" and isinstance(e.__cause__, ValueError) and str(e.__cause__) == "odd 3"
        assert process_all(risky, []) == []
        """,
        hints=["Keep the futures in a list in input order; after the `with` block every one is done.",
               "Collect `f.exception()` for each, then `raise RuntimeError(...) from errors[0]`."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor

        def process_all(fn, items, max_workers=4):
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(fn, item) for item in items]
            errors = [f.exception() for f in futures if f.exception() is not None]
            if errors:
                raise RuntimeError(f"{len(errors)} of {len(futures)} items failed") from errors[0]
            return [f.result() for f in futures]
        """,
        why="""An exception raised inside a submitted call is stored in its future; if nobody calls `result()` or `exception()`, it is simply garbage-collected with the future,
        and the failure leaves no trace, a common reason a "parallel" job silently processes half its data. Keeping the futures, in input order, makes every
        outcome inspectable after the `with` block (which waited for all of them). Reporting the count and chaining the first error (7.2) keeps the summary short
        while preserving a full traceback for debugging."""),
    predict("map, errors and order", "easy",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def score(doc):
            if doc == "corrupt":
                raise ValueError("cannot parse")
            return len(doc)

        docs = ["faq", "terms", "corrupt", "policy"]
        got = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            try:
                for value in pool.map(score, docs):
                    got.append(value)
            except ValueError as e:
                got.append(f"stopped: {e}")
        print(got)

        def safe(doc):
            try:
                return score(doc)
            except ValueError as e:
                return f"error: {e}"

        with ThreadPoolExecutor(max_workers=2) as pool:
            print(list(pool.map(safe, docs)))
        """,
        hints=["`map` yields results in input order and raises a call's exception when that position is reached."],
        why="""`map` yields results in order, and when it reaches a call that raised, it re-raises the exception there, so iteration stops and the later result is never seen
        (it was computed, but the loop ended). Catching errors **inside** the mapped function turns them into values, so every position gets a result: a simple,
        common pattern when you want `map`'s ordering without losing the batch."""),
)

section("medium", "Medium",
    write("A parallel map with retries", "medium", tag="GenAI",
        prompt="""Write `map_with_retry(fn, items, attempts=3, retry_on=(TimeoutError, ConnectionError), max_workers=8)` that calls `fn(item)` for each item on a thread pool,
        retrying each item up to `attempts` times in total when it raises one of `retry_on`. Return a list in input order of `{"item": ..., "ok": bool, "value": ... or
        None, "error": None or "ExceptionName: message", "attempts": n}`. Other exceptions are not retried.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def map_with_retry(fn, items, attempts=3, retry_on=(TimeoutError, ConnectionError), max_workers=8):
            pass
        """,
        tests="""
        tries = {}
        def flaky(x):
            tries[x] = tries.get(x, 0) + 1
            if x == "slow" and tries[x] < 3:
                raise TimeoutError("timed out")
            if x == "down":
                raise ConnectionError("refused")
            if x == "bad":
                raise ValueError("bad input")
            return x.upper()
        out = map_with_retry(flaky, ["ok", "slow", "down", "bad"], attempts=3)
        assert out[0] == {"item": "ok", "ok": True, "value": "OK", "error": None, "attempts": 1}
        assert out[1] == {"item": "slow", "ok": True, "value": "SLOW", "error": None, "attempts": 3}
        assert out[2] == {"item": "down", "ok": False, "value": None, "error": "ConnectionError: refused", "attempts": 3}
        assert out[3] == {"item": "bad", "ok": False, "value": None, "error": "ValueError: bad input", "attempts": 1}
        assert tries == {"ok": 1, "slow": 3, "down": 3, "bad": 1}
        """,
        hints=["Write a per-item function `one(item)` that loops over attempts and returns the record dict; then `list(pool.map(one, items))`.",
               "Catch `retry_on` and retry; catch other `Exception`s and stop at once."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor


        def map_with_retry(fn, items, attempts=3, retry_on=(TimeoutError, ConnectionError), max_workers=8):
            def one(item):
                for attempt in range(1, attempts + 1):
                    try:
                        return {"item": item, "ok": True, "value": fn(item), "error": None, "attempts": attempt}
                    except retry_on as e:
                        last = e
                    except Exception as e:
                        return {"item": item, "ok": False, "value": None, "error": f"{type(e).__name__}: {e}", "attempts": attempt}
                return {"item": item, "ok": False, "value": None, "error": f"{type(last).__name__}: {last}", "attempts": attempts}

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                return list(pool.map(one, items))
        """,
        why="""Putting the retry loop **inside** the task keeps each item's retries on its own worker, so one slow item does not delay the others, and wrapping every outcome in a
        record makes `map`'s ordered results safe to collect: no exception escapes, so nothing is lost. Retrying only transient errors (timeouts, dropped
        connections) and failing fast on others (a `ValueError` from bad input will fail every time) saves time and money. A production version adds backoff with
        jitter between attempts (13.3) and a shared rate limiter (problem 9)."""),
    fix("Workers that update a shared counter", "medium", tag="Data work",
        prompt="""`count_words_parallel(docs)` lets every worker add its counts into the module-level `TOTALS` dict with a read-modify-write, a race with real threads, and
        the totals keep growing across calls. Rewrite it so each worker **returns** its own `Counter` from `count_words(doc)` (a pure function that changes nothing
        outside) and the caller merges them; remove `TOTALS`.""",
        code="""
        from collections import Counter
        from concurrent.futures import ThreadPoolExecutor

        TOTALS = {}


        def count_words(doc):
            for word in doc.lower().split():
                TOTALS[word] = TOTALS.get(word, 0) + 1


        def count_words_parallel(docs, max_workers=4):
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                list(pool.map(count_words, docs))
            return dict(TOTALS)
        """,
        tests="""
        docs = ["Refunds take five days", "refunds after thirty days", "Shipping is free"]
        first = count_words_parallel(docs)
        assert first["refunds"] == 2 and first["days"] == 2 and first["shipping"] == 1
        assert count_words_parallel(docs) == first
        assert count_words("a b a") == Counter({"a": 2, "b": 1}) and "TOTALS" not in globals()
        """,
        hints=["`count_words` returns `Counter(doc.lower().split())`; the caller sums the counters with `sum(..., Counter())` or `update`."],
        solution="""
        from collections import Counter
        from concurrent.futures import ThreadPoolExecutor


        def count_words(doc):
            return Counter(doc.lower().split())


        def count_words_parallel(docs, max_workers=4):
            total = Counter()
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for counts in pool.map(count_words, docs):
                    total.update(counts)
            return dict(total)
        """,
        why="""`TOTALS[word] = TOTALS.get(word, 0) + 1` is a read followed by a write, so two threads counting the same word can both read 3 and both write 4 (14.1), and the
        module-level dict also carried counts over from earlier calls, so the second call returned doubled numbers. Returning results and merging them in the
        caller removes the shared state entirely: workers are pure functions, which are trivially thread-safe and easy to test, and the merge happens in one
        thread. This map-then-reduce shape is how distributed systems such as Spark and MapReduce avoid shared counters too. (Word counting is CPU-bound, so in
        practice it belongs on processes, 14.3; the pattern is the same.)"""),
    trace("The life of a Future", "medium",
        prompt="Fill in `state` after each marked line. These futures are created by hand, as executors do internally.",
        code="""
        from concurrent.futures import Future, CancelledError

        seen = []
        f = Future()
        f.add_done_callback(lambda fut: seen.append(fut.result()))
        state = (f.done(), f.running(), seen)  # row: "new future"
        f.set_result(42)
        state = (f.done(), f.result(), seen)  # row: "after set_result"
        f.add_done_callback(lambda fut: seen.append("late"))
        state = (f.cancel(), seen)  # row: "late callback, then cancel"
        g = Future()
        state = (g.cancel(), g.cancelled(), g.done())  # row: "cancel a pending future"
        try:
            g.result()
        except CancelledError:
            state = "CancelledError"  # row: "result of a cancelled future"
        """,
        trace_vars=["state"],
        hints=["Callbacks run when the result is set; a callback added after completion runs immediately. A finished future cannot be cancelled; a pending one can."],
        why="""A future starts pending; `set_result` (which the executor's worker calls) completes it and runs its callbacks with the future as argument. A callback added later
        runs at once, which is why callbacks are safe to add at any time. Cancelling a finished future fails and returns `False`; cancelling a pending one succeeds,
        marks it done and cancelled, and `result()` then raises `CancelledError`. In an executor, only calls that have not started can be cancelled, which is what
        `shutdown(cancel_futures=True)` relies on."""),
    write("Embed a corpus in parallel batches", "medium", tag="RAG",
        prompt="""Write `embed_corpus(texts, embed_batch, batch_size=32, max_workers=4)`: split `texts` into batches of `batch_size`, call `embed_batch(batch)` (returning one vector
        per text) for the batches on a thread pool, and return all vectors in the **original order**. Raise `ValueError(f"batch {i} returned {m} vectors for {n} texts")`
        if a batch returns the wrong number of vectors.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def embed_corpus(texts, embed_batch, batch_size=32, max_workers=4):
            pass
        """,
        tests="""
        batches_seen = []
        def embed_batch(batch):
            batches_seen.append(len(batch))
            return [[float(len(t)), float(t.count("a"))] for t in batch]
        texts = [f"doc {'a' * i}" for i in range(10)]
        vecs = embed_corpus(texts, embed_batch, batch_size=4, max_workers=2)
        assert vecs == [[float(len(t)), float(t.count("a"))] for t in texts]
        assert sorted(batches_seen) == [2, 4, 4] and embed_corpus([], embed_batch) == []
        def short(batch):
            return embed_batch(batch)[:-1] if len(batch) == 4 else embed_batch(batch)
        try:
            embed_corpus(texts, short, batch_size=4)
            assert False
        except ValueError as e:
            assert str(e) == "batch 0 returned 3 vectors for 4 texts"
        """,
        hints=["`batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]`; `pool.map(embed_batch, batches)` keeps batch order.",
               "Check each batch's output length against its input as you collect, using `enumerate`."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor


        def embed_corpus(texts, embed_batch, batch_size=32, max_workers=4):
            batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            vectors = []
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for i, (batch, out) in enumerate(zip(batches, pool.map(embed_batch, batches))):
                    if len(out) != len(batch):
                        raise ValueError(f"batch {i} returned {len(out)} vectors for {len(batch)} texts")
                    vectors.extend(out)
            return vectors
        """,
        why="""Embedding APIs accept batches, so the work splits naturally into batch calls that overlap their network waits on a thread pool. `map` returns batch results in
        submission order, so concatenating them restores the original text order without any bookkeeping, which is essential: a vector paired with the wrong text
        silently corrupts a search index. The length check guards against a provider dropping an input, which would otherwise shift every later vector by one.
        `batch_size` is set by the provider's limits (texts and tokens per request) and `max_workers` by its rate limits."""),
    write("A thread-safe token bucket", "medium", tag="GenAI",
        prompt="""Write `TokenBucket(rate, capacity, clock=time.monotonic)` for client-side rate limiting shared by many threads: it starts full, refills at `rate` tokens per
        second up to `capacity`, and `try_acquire(n=1)` takes `n` tokens and returns `True` if available, else returns `False` without taking any. Protect the state
        with a `threading.Lock`, since several threads call it. Also add `wait_time(n=1)`, the seconds until `n` tokens would be available (0.0 if now).""",
        code="""
        import threading, time

        class TokenBucket:
            pass
        """,
        tests="""
        now = [100.0]
        b = TokenBucket(rate=2.0, capacity=4, clock=lambda: now[0])
        assert [b.try_acquire() for _ in range(5)] == [True, True, True, True, False]
        assert b.wait_time() == 0.5
        now[0] += 1.0
        assert b.try_acquire(2) and not b.try_acquire()
        now[0] += 10
        assert b.try_acquire(4) and not b.try_acquire(1) and b.wait_time(3) == 1.5
        assert isinstance(b._lock, type(threading.Lock()))
        try:
            b.try_acquire(5)
            assert False
        except ValueError:
            pass
        """,
        hints=["Store `tokens` and `last` (the clock reading of the last refill); a private `_refill()` adds `(now - last) * rate`, capped at capacity.",
               "Do the refill and the check-and-take inside one `with self._lock:` block. Requests larger than `capacity` can never succeed: raise `ValueError`."],
        solution="""
        import threading, time


        class TokenBucket:
            def __init__(self, rate, capacity, clock=time.monotonic):
                self.rate, self.capacity, self.clock = rate, capacity, clock
                self.tokens = float(capacity)
                self.last = clock()
                self._lock = threading.Lock()

            def _refill(self):
                now = self.clock()
                self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
                self.last = now

            def try_acquire(self, n=1):
                if n > self.capacity:
                    raise ValueError(f"cannot acquire {n} tokens from a bucket of {self.capacity}")
                with self._lock:
                    self._refill()
                    if self.tokens >= n:
                        self.tokens -= n
                        return True
                    return False

            def wait_time(self, n=1):
                with self._lock:
                    self._refill()
                    return max(0.0, (n - self.tokens) / self.rate)
        """,
        why="""A token bucket allows short bursts (up to `capacity`) while holding the long-run rate to `rate` per second, which is how most API rate limits behave. The refill is
        computed lazily from elapsed time, so no background thread is needed. The lock makes "refill, check, take" one atomic step: without it, two threads could
        both see one remaining token and both take it, exceeding the limit. The injected clock makes the class deterministic to test (13.3). In a thread pool, a
        worker calls `try_acquire` before each request and sleeps for `wait_time()` when it fails; the asyncio version in 14.5 has the same logic."""),
    predict("Exceptions in raw threads", "medium",
        code="""
        import threading

        results = []

        def work(x):
            if x == 2:
                raise ValueError("bad item")
            results.append(x * 10)
            return "returned values are discarded"

        caught = []
        threading.excepthook = lambda args: caught.append((args.exc_type.__name__, str(args.exc_value), args.thread.name))
        threads = [threading.Thread(target=work, args=(i,), name=f"worker-{i}") for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print(sorted(results), caught)
        print("main thread continues", threading.current_thread().name)
        """,
        hints=["An exception in a thread's target is passed to `threading.excepthook`; it does not propagate to the code that started or joined the thread."],
        why="""The failing thread's exception goes to `threading.excepthook` (by default it prints a traceback to standard error), `join()` returns normally, and the main thread
        never learns about it unless something records it, which is how errors disappear in thread-based code. Return values are discarded too, so results travel
        through shared structures. Executors solve both problems by storing the result or the exception in a future (problem 3)."""),
)

section("hard", "Hard",
    write("A pipeline of parallel stages", "hard", tag="RAG",
        prompt="""Write `run_pipeline(items, stages, max_workers=4)` where `stages` is a list of `(name, fn)`. Each stage runs `fn` on every item still alive, in parallel on a
        thread pool, in input order. An item whose stage raises is dropped from later stages and recorded. Return `{"results": [final values of surviving items, in
        input order], "failed": [(index, stage_name, "ExceptionName: message"), ...] in index order}`.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        def run_pipeline(items, stages, max_workers=4):
            pass
        """,
        tests="""
        def fetch(url):
            if "404" in url:
                raise LookupError("not found")
            return f"<p>{url.split('/')[-1]} text</p>"

        def clean(html):
            text = html.replace("<p>", "").replace("</p>", "")
            if text.startswith("empty"):
                raise ValueError("no content")
            return text

        def chunk(text):
            return text.split()

        urls = ["https://x.io/faq", "https://x.io/404", "https://x.io/empty", "https://x.io/terms"]
        out = run_pipeline(urls, [("fetch", fetch), ("clean", clean), ("chunk", chunk)], max_workers=2)
        assert out["results"] == [["faq", "text"], ["terms", "text"]]
        assert out["failed"] == [(1, "fetch", "LookupError: not found"), (2, "clean", "ValueError: no content")]
        assert run_pipeline([], [("fetch", fetch)]) == {"results": [], "failed": []}
        assert run_pipeline([1, 2], []) == {"results": [1, 2], "failed": []}
        """,
        hints=["Track `alive` as a list of `(index, value)` pairs. For each stage, submit `fn(value)` for each, then rebuild `alive` from the futures in order.",
               "`future.exception()` tells you whether to keep the item or record the failure."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor


        def run_pipeline(items, stages, max_workers=4):
            alive = list(enumerate(items))
            failed = []
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for name, fn in stages:
                    futures = [(i, pool.submit(fn, value)) for i, value in alive]
                    alive = []
                    for i, future in futures:
                        error = future.exception()
                        if error is None:
                            alive.append((i, future.result()))
                        else:
                            failed.append((i, name, f"{type(error).__name__}: {error}"))
            return {"results": [value for _, value in alive], "failed": sorted(failed)}
        """,
        why="""Ingestion jobs are pipelines (fetch, clean, chunk, embed), and each stage is a batch of independent calls, so each runs in parallel on one shared pool. Carrying the
        original index with every value is what lets results and failures be reported in input order and traced back to the input, however the threads
        interleave; failed items leave the pipeline at the stage that failed and are recorded with that stage's name, which tells the operator where to look.
        Processing stage by stage is simple and keeps memory bounded per stage; a streaming design (each item flows on as soon as it finishes a stage) improves
        latency and is what queues between stages or asyncio tasks (14.5) provide."""),
    fix("Read the code: a thread-per-document scraper", "hard", tag="Data work",
        prompt="""This scraper starts one raw `Thread` per URL (thousands of threads for a big crawl), collects results in a global list in completion order, loses every
        exception (the thread just dies), and returns before checking that all threads finished. Rewrite `scrape(urls, fetch, parse, max_workers=8)` with a
        `ThreadPoolExecutor` so it returns `{"pages": [parsed result per URL, in input order, None for failures], "errors": {url: "ExceptionName: message"}}`, with
        no module-level state and no raw threads.""",
        code="""
        import threading

        PAGES = []


        def _work(url, fetch, parse):
            html = fetch(url)
            PAGES.append(parse(html))


        def scrape(urls, fetch, parse, max_workers=8):
            threads = [threading.Thread(target=_work, args=(u, fetch, parse)) for u in urls]
            for t in threads:
                t.start()
            return {"pages": PAGES, "errors": {}}
        """,
        tests="""
        import threading
        threading.excepthook = lambda args: None
        def fetch(url):
            if url.endswith("down"):
                raise ConnectionError("refused")
            return f"<title>{url.rsplit('/', 1)[-1]}</title>"
        def parse(html):
            if "broken" in html:
                raise ValueError("no title")
            return html[7:-8]
        urls = ["https://s.io/a", "https://s.io/down", "https://s.io/broken", "https://s.io/b"]
        out = scrape(urls, fetch, parse, max_workers=3)
        assert out == {"pages": ["a", None, None, "b"], "errors": {"https://s.io/down": "ConnectionError: refused", "https://s.io/broken": "ValueError: no title"}}
        assert scrape(urls[:1], fetch, parse) == {"pages": ["a"], "errors": {}}
        assert "threading.Thread(" not in __source__ and "PAGES" not in __source__
        """,
        hints=["One task per URL that does `parse(fetch(url))`; submit them all, keep the futures in input order.",
               "The executor's `with` block waits for every task, so no `join` bookkeeping is needed."],
        solution="""
        from concurrent.futures import ThreadPoolExecutor


        def _work(url, fetch, parse):
            return parse(fetch(url))


        def scrape(urls, fetch, parse, max_workers=8):
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [(url, pool.submit(_work, url, fetch, parse)) for url in urls]
            pages, errors = [], {}
            for url, future in futures:
                error = future.exception()
                if error is None:
                    pages.append(future.result())
                else:
                    pages.append(None)
                    errors[url] = f"{type(error).__name__}: {error}"
            return {"pages": pages, "errors": errors}
        """,
        why="""Each defect is a lesson section. A thread per URL creates thousands of threads, each with its own stack, and hammers the target site; a pool of 8 bounds both memory
        and load. The global list mixed results from different calls and stored them in completion order, so page `i` was not URL `i`; returning values through
        futures and rebuilding in input order fixes both. Raw threads swallow exceptions into `excepthook`, so failures were invisible; futures keep them for the
        caller. And `scrape` returned before the threads finished, so callers saw a partial list; the executor's `with` block waits for all tasks."""),
    predict("as_completed, wait and timeouts", "hard",
        code="""
        from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_EXCEPTION, ALL_COMPLETED

        def job(x):
            if x == 3:
                raise RuntimeError("job 3 failed")
            return x * x

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(job, x) for x in range(5)]
            done, pending = wait(futures, return_when=ALL_COMPLETED)
            print(len(done), len(pending), sorted(f.result() for f in done if f.exception() is None))
            done, pending = wait(futures, return_when=FIRST_EXCEPTION)
            print(len(done) >= 1, [type(f.exception()).__name__ for f in futures if f.exception()])
            values = sorted(f.result() for f in as_completed(futures) if not f.exception())
            print(values, futures[2].result(timeout=1))
            print(sum(1 for _ in as_completed(futures, timeout=5)), all(f.done() for f in futures))
        """,
        hints=["`wait` returns two sets, done and not done. `as_completed` yields each future once, in completion order. On this site every future completes at submission."],
        why="""`wait` splits futures into finished and unfinished sets; with all of them complete, everything is in `done`, and the failed one is among them, holding its exception.
        `FIRST_EXCEPTION` returns as soon as one future has failed (or all are done). Sorting the results from `as_completed` makes the output independent of the
        completion order, which varies between runs with real threads, a habit worth keeping whenever results are printed or asserted. `result(timeout=...)` and
        `as_completed(timeout=...)` raise `TimeoutError` if futures do not finish in time, the tools for bounding how long a batch may wait."""),
)

section("interview", "Interview questions",
    explain("Why use a ThreadPoolExecutor rather than creating threads yourself?", "medium", tag="Interview",
        why="""An executor bounds concurrency with a fixed pool, so a list of 10,000 items does not create 10,000 threads or overload the service being called; it reuses threads
        instead of paying creation costs per task; it returns **futures**, so each call's return value or exception comes back to the caller with its traceback, where
        raw threads discard return values and only print exceptions; it offers `map` (ordered results) and `as_completed` (completion order), timeouts, cancellation of
        not-yet-started work and `wait` policies; and as a context manager it guarantees all work has finished (or been cancelled) when the block ends. Swapping
        `ThreadPoolExecutor` for `ProcessPoolExecutor` moves CPU-bound work to processes with the same code. Raw threads remain appropriate for long-lived background
        loops."""),
    explain("How do you make code safe to call from several threads?", "medium", tag="Interview",
        why="""First minimise shared mutable state: make tasks pure functions of their inputs that return results, and combine results in one thread afterwards; use immutable
        data (tuples, frozen dataclasses) for shared configuration. For state that must be shared (caches, counters, rate limiters, connection pools), guard every
        compound operation with a `threading.Lock`, keeping critical sections short and never holding a lock across slow I/O; acquire several locks in one global order to
        avoid deadlocks. Use thread-safe structures (`queue.Queue` for hand-offs, `threading.Event` for signals) instead of hand-made flags. Check that the libraries you
        share are documented as thread-safe (HTTP clients usually are; database connections often are not, so use a pool or one per thread, or `threading.local`). Test
        with stress tests and deterministic interleaving tools, and remember that the GIL never made compound operations atomic, and free-threaded Python removes even
        the incidental protection it gave."""),
    explain("A colleague used threads to speed up a CPU-heavy feature extraction and it got slower. Explain and fix it.", "hard", tag="Interview",
        why="""With the GIL, only one thread executes Python bytecode at a time, so pure-Python CPU work cannot run in parallel on threads; it runs one thread at a time with extra
        overhead from switching and lock contention, which makes it slower than a plain loop. Threads help only when work waits (I/O) or runs in C code that releases the
        GIL. The fix depends on the work: vectorise with NumPy or pandas, whose inner loops run in C (often several times faster on its own, and some operations use several
        cores); move the work to processes with `ProcessPoolExecutor`, chunking the input so each task is large enough to amortise the cost of sending data between processes
        (14.3); or, on a free-threaded Python build with compatible libraries, threads do run in parallel. Measure before and after with wall time and CPU time, and check
        Amdahl's law: if part of the pipeline is serial (reading one file, writing one output), that part bounds the speed-up."""),
)

recap(
    "Prefer `concurrent.futures` to raw threads: executors bound concurrency, and futures carry results and exceptions back.",
    "`submit` returns a `Future` (`result()` re-raises, `exception()` inspects); `map` keeps input order and raises at the failing item; `as_completed` yields in completion order.",
    "Keep a dict from future to input, rebuild outputs in input order, and turn per-item errors into data so a batch survives failures.",
    "Avoid shared mutable state: return results and merge them; when state must be shared, guard compound operations with a `Lock`, briefly.",
    "Size I/O thread pools by latency and rate limits (Little's law), share thread-safe clients, and always set timeouts.",
)
