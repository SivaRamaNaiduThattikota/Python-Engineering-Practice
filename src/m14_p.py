from lesson import *
from diagrams import *

lesson(
    id="m14-p", num="14.P", title="Module 14 practice set and mini project",
    intro="Mixed problems from all of Module 14: choosing between threads, processes and asyncio, futures, picklability, the event "
          "loop, races at await points, limits, timeouts and queues. Then a mini project that needs all of it: an async evaluation "
          "runner that calls a model concurrently under a concurrency limit and a request spacing, with timeouts and retries, scores "
          "answers in a process pool, and writes results incrementally so a run can resume.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project async evaluation runner semaphore rate spacing timeout retry run_in_executor process pool to_thread jsonl resume race await lock check-then-act pipeline queues",
)

section("how", "How to use this page",
    fig(stage_map(14, "an async evaluation runner"), "Module 14 at a glance: when concurrency helps, then threads, processes and asyncio, building up to an evaluation runner."),
    p("""For any slow program, first ask **what it waits on** (14.1): computation calls for processes (14.3) or vectorised code, waiting calls for threads (14.2) or
    asyncio (14.4). Then ask **what it shares**: return results instead of sharing state, protect what must be shared, and remember that in asyncio a race can
    happen at every `await`. Finally ask **what can go wrong at scale** (14.5): limits, rate limits, timeouts, transient failures, back-pressure and shutdown."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all of them in the kind of job that runs every time a prompt or model changes."""),
)

section("set", "Practice set",
    predict("Mixing asyncio, threads and processes", "easy",
        code="""
        import asyncio
        from concurrent.futures import ProcessPoolExecutor

        def tokenize(text):
            return len(text.split())

        def blocking_lookup(key):
            return {"refund": "5 days"}.get(key, "unknown")

        async def fetch(name, seconds):
            await asyncio.sleep(seconds)
            return name

        async def main():
            loop = asyncio.get_running_loop()
            with ProcessPoolExecutor(max_workers=2) as pool:
                counts = await asyncio.gather(*(loop.run_in_executor(pool, tokenize, t) for t in ["a b c", "d e"]))
            looked_up = await asyncio.to_thread(blocking_lookup, "refund")
            fetched = await asyncio.gather(fetch("x", 1.5), fetch("y", 0.5))
            return counts, looked_up, fetched, loop.time()

        print(asyncio.run(main()))
        """,
        hints=["`run_in_executor` and `to_thread` return awaitables, so executor work fits into `gather`. On this site, executor work takes no simulated time."],
        why="""`loop.run_in_executor(pool, fn, *args)` runs a function in a thread or process pool and returns an awaitable, so CPU-bound work (tokenising here) can be awaited from
        async code without blocking the loop; `asyncio.to_thread` is the shortcut for the default thread pool, the right tool for a blocking library call. Only the
        async sleeps advance the simulated clock, and the two run concurrently, so the total is 1.5 seconds. On a real machine the executor work takes real time,
        but it still does not block other tasks."""),
    write("gather for a dict of awaitables", "easy", tag="GenAI",
        prompt="""Write `async def gather_dict(aws)` taking a dict from names to awaitables and returning `(results, errors)`: two dicts keyed by name, in the input's key order, where
        `errors` holds `"ExceptionName: message"` for awaitables that raised. All run concurrently.""",
        code="""
        import asyncio

        async def gather_dict(aws):
            pass
        """,
        tests="""
        import asyncio
        async def source(value, seconds, fail=False):
            await asyncio.sleep(seconds)
            if fail:
                raise TimeoutError("too slow")
            return value
        async def main():
            loop = asyncio.get_running_loop()
            out = await gather_dict({"faq": source(["f1"], 1.0), "web": source(None, 2.0, fail=True), "wiki": source(["w1"], 0.5)})
            return out, loop.time()
        (results, errors), t = asyncio.run(main())
        assert results == {"faq": ["f1"], "wiki": ["w1"]} and list(results) == ["faq", "wiki"]
        assert errors == {"web": "TimeoutError: too slow"} and t == 2.0
        assert asyncio.run(gather_dict({})) == ({}, {})
        """,
        hints=["`names = list(aws)`; `values = await asyncio.gather(*aws.values(), return_exceptions=True)`; then split by `isinstance(v, Exception)`."],
        solution="""
        import asyncio


        async def gather_dict(aws):
            names = list(aws)
            values = await asyncio.gather(*aws.values(), return_exceptions=True)
            results, errors = {}, {}
            for name, value in zip(names, values):
                if isinstance(value, Exception):
                    errors[name] = f"{type(value).__name__}: {value}"
                else:
                    results[name] = value
            return results, errors
        """,
        why="""Naming concurrent calls is clearer than tracking positions, especially when they are different operations (several retrievers, several tools). Dicts keep insertion
        order and `gather` keeps argument order, so zipping the keys with the results is safe. Separating results from errors gives the caller a ready answer for "what
        worked" and a report of what did not."""),
    fix("Calling a coroutine from synchronous code", "easy", tag="Data work",
        prompt="""`load_report` is called from a normal (synchronous) script and should return the report dict, but it returns a coroutine object instead, and Python warns that the
        coroutine was never awaited. Fix it so synchronous callers get the result.""",
        code="""
        import asyncio

        async def fetch_report(day):
            await asyncio.sleep(0.5)
            return {"day": day, "rows": 120}

        def load_report(day):
            return fetch_report(day)
        """,
        tests="""
        assert load_report("2025-03-01") == {"day": "2025-03-01", "rows": 120}
        assert load_report("2025-03-02")["rows"] == 120
        """,
        hints=["At the boundary between synchronous and async code, run the coroutine with `asyncio.run(...)`."],
        solution="""
        import asyncio

        async def fetch_report(day):
            await asyncio.sleep(0.5)
            return {"day": day, "rows": 120}

        def load_report(day):
            return asyncio.run(fetch_report(day))
        """,
        why="""Calling an `async def` function only creates a coroutine; something must run it on an event loop. In a synchronous program, `asyncio.run` is that boundary: it starts a
        loop, runs the coroutine and returns its result. Call it at the top of the program (or once per synchronous entry point), never from inside async code, where
        you `await` instead; in a real program, `asyncio.run` inside a running loop raises `RuntimeError`. Notebooks already run a loop, so there you `await` directly."""),
    predict("Which tool for which job", "medium",
        code="""
        def choose(wait_fraction, n_tasks, async_libs):
            if wait_fraction < 0.2:
                return "processes"
            if n_tasks > 500 and async_libs:
                return "asyncio"
            return "threads"

        jobs = {
            "tokenise 10M lines": (0.02, 10_000, False),
            "5,000 LLM calls, async SDK": (0.98, 5_000, True),
            "50 downloads with requests": (0.95, 50, False),
            "2,000 S3 uploads, sync SDK": (0.9, 2_000, False),
            "grid search on 4 cores": (0.05, 24, False),
        }
        for name, args in jobs.items():
            print(f"{name:28} {choose(*args)}")
        """,
        hints=["Mostly computing means processes; mostly waiting means threads, or asyncio when there are many tasks and async libraries."],
        why="""The heuristic encodes the module's decision rule. Tokenising and grid search compute almost all the time, so processes. Thousands of LLM calls with an async SDK suit
        asyncio's cheap concurrency. Fifty downloads through `requests` (a blocking library) are a natural fit for a thread pool. Thousands of uploads through a
        synchronous SDK also go to threads (with a bounded pool), because asyncio would need `to_thread` for every call anyway. Real decisions add measurement, memory
        limits and what the rest of the codebase already uses."""),
    write("A two-stage async pipeline with queues", "medium", tag="RAG",
        prompt="""Write `async def pipeline(urls, fetch, parse, fetchers=2, parsers=1)`: `fetchers` worker tasks take `(i, url)` from a first queue, `await fetch(url)`, and put `(i, html)`
        on a second queue; `parsers` workers take from the second queue and store `await parse(html)` in the result list at index `i`. Return the results in input order.
        Use `join()` on each queue in turn, then cancel all workers.""",
        code="""
        import asyncio

        async def pipeline(urls, fetch, parse, fetchers=2, parsers=1):
            pass
        """,
        tests="""
        import asyncio
        async def fetch(url):
            await asyncio.sleep(1.0)
            return f"<p>{url}</p>"
        async def parse(html):
            await asyncio.sleep(0.25)
            return html[3:-4].upper()
        async def main():
            loop = asyncio.get_running_loop()
            out = await pipeline(["a", "b", "c", "d"], fetch, parse, fetchers=2, parsers=1)
            return out, loop.time()
        out, t = asyncio.run(main())
        assert out == ["A", "B", "C", "D"] and t == 2.5
        assert asyncio.run(pipeline([], fetch, parse)) == []
        """,
        hints=["Two queues; fetch workers `get` from the first and `put` to the second, calling `task_done` on the first in a `finally`.",
               "Put all urls, `await q1.join()` (all fetched), then `await q2.join()` (all parsed), then cancel and gather the workers."],
        solution="""
        import asyncio


        async def pipeline(urls, fetch, parse, fetchers=2, parsers=1):
            q1, q2 = asyncio.Queue(), asyncio.Queue()
            results = [None] * len(urls)

            async def fetch_worker():
                while True:
                    i, url = await q1.get()
                    try:
                        await q2.put((i, await fetch(url)))
                    finally:
                        q1.task_done()

            async def parse_worker():
                while True:
                    i, html = await q2.get()
                    try:
                        results[i] = await parse(html)
                    finally:
                        q2.task_done()

            workers = [asyncio.create_task(fetch_worker()) for _ in range(fetchers)]
            workers += [asyncio.create_task(parse_worker()) for _ in range(parsers)]
            try:
                for pair in enumerate(urls):
                    await q1.put(pair)
                await q1.join()
                await q2.join()
            finally:
                for w in workers:
                    w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
            return results
        """,
        why="""Each stage gets its own concurrency (two fetchers for the slow network step, one parser), and items flow on as soon as they are fetched, so parsing overlaps fetching:
        two waves of fetching take 2 seconds, and the last parse finishes a quarter of a second after the last fetch, at 2.5 seconds. Joining the first queue and then the
        second guarantees that every item has passed both stages, because each fetched item is put on the second queue before the first queue's `task_done`. Indices
        keep the output in input order. Ingestion systems are chains of such stages, sometimes with a queue service between machines instead of `asyncio.Queue`."""),
    fix("A race at an await point", "medium", tag="GenAI",
        prompt="""`get_embedding` caches embeddings, but when five tasks ask for the same text at once, all five see an empty cache, all five call the API, and the cache is written five
        times: the check and the write are separated by an `await`. Fix it so concurrent requests for the same key make **one** call: store the in-flight task in the cache
        and let later callers await it.""",
        code="""
        import asyncio

        CACHE = {}

        async def get_embedding(text, embed):
            if text not in CACHE:
                CACHE[text] = await embed(text)
            return CACHE[text]
        """,
        tests="""
        import asyncio
        CACHE.clear()
        calls = []
        async def embed(text):
            calls.append(text)
            await asyncio.sleep(1.0)
            return [float(len(text))]
        async def main():
            loop = asyncio.get_running_loop()
            out = await asyncio.gather(*(get_embedding("refund", embed) for _ in range(5)), get_embedding("ship", embed))
            again = await get_embedding("refund", embed)
            return out, again, loop.time()
        out, again, t = asyncio.run(main())
        assert out == [[6.0]] * 5 + [[4.0]] and again == [6.0] and t == 1.0
        assert calls == ["refund", "ship"]
        """,
        hints=["Store `asyncio.create_task(embed(text))` in the cache **before** awaiting it; every caller then does `return await CACHE[text]` (awaiting a finished task is instant)."],
        solution="""
        import asyncio

        CACHE = {}

        async def get_embedding(text, embed):
            task = CACHE.get(text)
            if task is None:
                task = asyncio.create_task(embed(text))
                CACHE[text] = task
            return await task
        """,
        why="""asyncio has no preemption, but it has **switch points**: every `await`. Between the membership test and the assignment, the original code awaited the API, so every other
        task ran its own test meanwhile and found the cache empty: a check-then-act race, the asyncio version of 14.1's lost update. Storing the task before awaiting
        it closes the gap, because there is no `await` between the check and the insert, so the five callers share one call; finished tasks keep their result, so later
        callers get it immediately. A failed task would stay cached here; 14.5's single flight removes entries on completion, which a production cache combines with a
        TTL."""),
    trace("asyncio.Lock and Event", "medium",
        prompt="Fill in `log` after the marked line.",
        code="""
        import asyncio

        async def scenario():
            lock, ready, log = asyncio.Lock(), asyncio.Event(), []
            loop = asyncio.get_running_loop()

            async def writer(name, seconds):
                await ready.wait()
                async with lock:
                    log.append(f"{name} in @{loop.time():g}")
                    await asyncio.sleep(seconds)
                    log.append(f"{name} out @{loop.time():g}")

            tasks = [asyncio.create_task(writer(n, s)) for n, s in [("a", 1), ("b", 0.5), ("c", 2)]]
            await asyncio.sleep(1)
            log.append(f"ready @{loop.time():g}")
            ready.set()
            await asyncio.gather(*tasks)
            return log

        log = asyncio.run(scenario())  # row: "lock queue"
        """,
        trace_vars=["log"],
        hints=["All writers wait on the event until it is set at 1 second. The lock lets one writer in at a time, in the order they asked for it."],
        why="""No writer can start before the event is set, so `ready` is logged first, at 1 second. Then the writers ask for the lock in creation order; the lock is fair, so they
        enter one after another, each holding it across its sleep: `a` from 1 to 2, `b` from 2 to 2.5, `c` from 2.5 to 4.5. Holding a lock across an `await` serialises
        the tasks completely, which is correct for writing to a shared file and wasteful for anything that could overlap."""),
    write("Timeouts with a fallback answer", "medium", tag="GenAI",
        prompt="""Write `async def answer_with_fallback(primary, fallback, question, budget=2.0)`: try `await primary(question)` within `budget` seconds; on timeout or any `Exception`, call
        `await fallback(question)` with the **remaining** budget (at least 0.1 seconds). Return `(answer, source)` with `source` `"primary"` or `"fallback"`; if the fallback
        also fails or times out, return `("Sorry, try again later.", "none")`.""",
        code="""
        import asyncio

        async def answer_with_fallback(primary, fallback, question, budget=2.0):
            pass
        """,
        tests="""
        import asyncio
        def model(name, seconds, fail=False):
            async def call(q):
                await asyncio.sleep(seconds)
                if fail:
                    raise ConnectionError(f"{name} down")
                return f"{name}: {q}"
            return call
        async def run(primary, fallback, budget=2.0):
            loop = asyncio.get_running_loop()
            out = await answer_with_fallback(primary, fallback, "refund?", budget)
            return out, round(loop.time(), 3)
        assert asyncio.run(run(model("big", 1.0), model("small", 0.2))) == (("big: refund?", "primary"), 1.0)
        assert asyncio.run(run(model("big", 5.0), model("small", 0.05))) == (("small: refund?", "fallback"), 2.05)
        assert asyncio.run(run(model("big", 0.5, fail=True), model("small", 0.2))) == (("small: refund?", "fallback"), 0.7)
        assert asyncio.run(run(model("big", 1.5, fail=True), model("small", 1.0))) == (("Sorry, try again later.", "none"), 2.0)
        """,
        hints=["Record `start = loop.time()`; the remaining budget is `max(0.1, budget - (loop.time() - start))`.",
               "Use `asyncio.wait_for(...)` or `async with asyncio.timeout(...)` for each attempt, catching `Exception` (which includes `TimeoutError`)."],
        solution="""
        import asyncio


        async def answer_with_fallback(primary, fallback, question, budget=2.0):
            loop = asyncio.get_running_loop()
            start = loop.time()
            try:
                return await asyncio.wait_for(primary(question), timeout=budget), "primary"
            except Exception:
                pass
            remaining = max(0.1, budget - (loop.time() - start))
            try:
                return await asyncio.wait_for(fallback(question), timeout=remaining), "fallback"
            except Exception:
                return "Sorry, try again later.", "none"
        """,
        why="""A latency budget is shared across the attempts: when the big model times out at 2 seconds, the fallback still gets a small minimum (0.1 seconds) so the user is not left
        without an answer, and when the primary fails fast at 0.5 seconds, the fallback gets the remaining 1.5. Catching `Exception` covers both timeouts and failures,
        while letting cancellation propagate. Serving a smaller model or a cached answer when the main one is slow or down is a standard degradation strategy for LLM
        products; the source field lets you monitor how often it happens."""),
    explain("Your async service's latency spikes for all users whenever one user uploads a large PDF. What is likely happening and how do you fix it?", "medium", tag="Interview",
        why="""PDF parsing is CPU-bound and probably runs directly inside a coroutine (or calls a synchronous parsing library), so it never yields: while it runs, the event loop cannot
        serve any other request, and every in-flight request waits, which shows up as a latency spike for everyone. Fix it by moving the work off the loop: run the parser
        in a process pool with `await loop.run_in_executor(pool, parse, path)` (processes, because it is CPU-bound and the GIL would serialise threads), or hand it to a
        background job queue (Celery, RQ, a cloud queue) and return a job id; for blocking I/O-heavy libraries, `asyncio.to_thread` suffices. Also limit concurrent heavy jobs
        with a semaphore so they cannot exhaust the pool, set size limits on uploads, and enable asyncio debug mode or a slow-callback monitor to catch future blocking calls."""),
    explain("Explain the difference between a race condition in threaded code and one in asyncio code.", "hard", tag="Interview",
        why="""In threaded code, the operating system can switch threads between almost any two bytecode instructions (and on free-threaded Python, threads truly run at once), so any
        compound operation on shared state (read-modify-write, check-then-act) can interleave with another thread's; protection needs locks around the critical
        section. In asyncio, all tasks run in one thread and switch only at `await` (or `async for`/`async with`) points, so code **between** awaits is atomic with respect
        to other tasks, which removes most low-level races; but a check-then-act that spans an `await` (checking a cache, then awaiting the computation, then writing) can
        still interleave with other tasks at that await, causing duplicated work or inconsistent state. The fixes are to avoid awaiting between check and act (store a task
        or future first, as in single flight), to use `asyncio.Lock` around the whole sequence, or to restructure so each task owns its data. asyncio locks must not be used
        across threads, and thread locks must not be held across awaits."""),
)

section("project", "Mini project: an async evaluation runner",
    fig(flowchart({
        "case": ("start", 0, 0, "next case"),
        "done": ("ask", 0, 1, "already in done_ids?"),
        "skip": ("step", 1, 1, "skip it"),
        "call": ("accent", 0, 2, "semaphore + spacing,|call with a timeout"),
        "err": ("ask", 0, 3, "did it answer?"),
        "retry": ("ask", 1, 3, "transient error and|attempts left?"),
        "fail": ("bad", 2, 3, "write ok: false"),
        "score": ("accent2", 0, 4, "score in the|process pool"),
        "write": ("end", 0, 5, "write ok: true"),
    }, [("case", "done"), ("done", "skip", "yes"), ("done", "call", "no"), ("call", "err"), ("err", "retry", "no"),
        ("retry", "call", "yes", {"route": [(1, 2)]}), ("retry", "fail", "no"), ("err", "score", "yes"), ("score", "write")],
        cell=(220, 78), label="each case in the evaluation runner"),
        "The runner per case: skip what is done, limit and space the calls, retry only transient errors, and score off the event loop."),
    p("""Every prompt or model change triggers an evaluation run: hundreds of questions sent to a model, each answer scored against an expected answer. The runner must use the
    provider's capacity without exceeding it, survive timeouts and transient failures, keep the CPU-heavy scoring off the event loop, write each result as soon as it is
    known, and skip the cases a previous, interrupted run already finished. Build it from the pieces of this module."""),
    write("Run an evaluation concurrently and resumably", "hard", key="async-eval-runner", tag="Project",
        prompt="""Implement the following.

        - **`score_answer(answer, expected)`** (top-level, so a process can receive it): the fraction of the expected answer's words (lower-cased) found in the answer, rounded to 3.
        - **`async def run_eval(cases, model, out, *, limit=4, spacing=0.0, timeout=10.0, attempts=3, done_ids=frozenset(), pool=None)`** where each case is `{"id", "question",
          "expected"}`:
          - skip cases whose id is in `done_ids`;
          - at most `limit` model calls at once (a semaphore), and successive call **starts** at least `spacing` seconds apart (a lock plus the time of the last start);
          - each attempt `await model(question)` has a timeout of `timeout` seconds; `TimeoutError` and `ConnectionError` are retried up to `attempts` calls in total,
            other exceptions are not;
          - score successful answers with `score_answer` in `pool` (a `ProcessPoolExecutor`) via `loop.run_in_executor`;
          - as each case finishes, append one JSON line (a string from `json.dumps`) to `out`: `{"id", "ok": true, "answer", "score", "attempts"}` or `{"id", "ok": false,
            "error": "ExceptionName", "attempts"}`;
          - return `{"run": n_run, "skipped": n_skipped, "ok": n_ok, "failed": n_failed, "mean_score": mean of ok scores rounded to 3 (0.0 if none), "elapsed": loop time
            taken}`.""",
        code="""
        import asyncio, json
        from concurrent.futures import ProcessPoolExecutor


        def score_answer(answer, expected):
            pass


        async def run_eval(cases, model, out, *, limit=4, spacing=0.0, timeout=10.0, attempts=3, done_ids=frozenset(), pool=None):
            pass
        """,
        tests="""
        import asyncio, json
        from concurrent.futures import ProcessPoolExecutor
        tries, starts = {}, []
        state = {"active": 0, "peak": 0}
        async def model(question):
            loop = asyncio.get_running_loop()
            starts.append(loop.time())
            tries[question] = tries.get(question, 0) + 1
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            try:
                if question == "flaky" and tries[question] < 3:
                    raise ConnectionError("reset")
                if question == "hangs":
                    await asyncio.sleep(100)
                if question == "refused":
                    raise PermissionError("blocked by policy")
                await asyncio.sleep(1.0)
                return {"refunds": "Refunds take five business days", "shipping": "Shipping is free in the EU", "flaky": "it worked"}.get(question, "no idea")
            finally:
                state["active"] -= 1
        cases = [
            {"id": "c1", "question": "refunds", "expected": "five business days"},
            {"id": "c2", "question": "shipping", "expected": "free shipping worldwide"},
            {"id": "c3", "question": "flaky", "expected": "it worked"},
            {"id": "c4", "question": "hangs", "expected": "x"},
            {"id": "c5", "question": "refused", "expected": "x"},
            {"id": "c6", "question": "already done", "expected": "x"},
        ]
        out = []
        async def main():
            with ProcessPoolExecutor(max_workers=2) as pool:
                return await run_eval(cases, model, out, limit=2, spacing=0.25, timeout=3.0, attempts=3, done_ids={"c6"}, pool=pool)
        summary = asyncio.run(main())
        assert summary == {"run": 5, "skipped": 1, "ok": 3, "failed": 2, "mean_score": 0.889, "elapsed": summary["elapsed"]}
        records = {r["id"]: r for r in map(json.loads, out)}
        assert records["c1"] == {"id": "c1", "ok": True, "answer": "Refunds take five business days", "score": 1.0, "attempts": 1}
        assert records["c2"]["score"] == 0.667 and records["c3"] == {"id": "c3", "ok": True, "answer": "it worked", "score": 1.0, "attempts": 3}
        assert records["c4"] == {"id": "c4", "ok": False, "error": "TimeoutError", "attempts": 3}
        assert records["c5"] == {"id": "c5", "ok": False, "error": "PermissionError", "attempts": 1}
        assert len(out) == 5 and "c6" not in records and state["peak"] == 2
        assert all(b - a >= 0.25 - 1e-9 for a, b in zip(starts, starts[1:]))
        assert score_answer("Free shipping!", "free shipping worldwide") == 0.667 and score_answer("x", "") == 0.0
        empty = []
        assert asyncio.run(run_eval([], model, empty))["mean_score"] == 0.0 and empty == []
        """,
        hints=["Spacing: keep `last = [None]` and an `asyncio.Lock`; inside the lock, sleep until `last[0] + spacing` if needed, then record the start time.",
               "Per case: `async with sem:` then the attempt loop, each attempt spacing first and then `async with asyncio.timeout(timeout): answer = await model(...)`.",
               "Scoring: `await loop.run_in_executor(pool, score_answer, answer, expected)`; append `json.dumps(record)` to `out` when the case is finished."],
        solution="""
        import asyncio, json
        from concurrent.futures import ProcessPoolExecutor


        def score_answer(answer, expected):
            words = expected.lower().split()
            if not words:
                return 0.0
            have = set(answer.lower().replace("!", " ").replace(".", " ").replace(",", " ").split())
            return round(sum(w in have for w in words) / len(words), 3)


        async def run_eval(cases, model, out, *, limit=4, spacing=0.0, timeout=10.0, attempts=3, done_ids=frozenset(), pool=None):
            loop = asyncio.get_running_loop()
            start = loop.time()
            sem, gate, last = asyncio.Semaphore(limit), asyncio.Lock(), [None]
            scores, failed = [], [0]

            async def wait_turn():
                async with gate:
                    if last[0] is not None and spacing > 0:
                        delay = last[0] + spacing - loop.time()
                        if delay > 0:
                            await asyncio.sleep(delay)
                    last[0] = loop.time()

            async def one(case):
                async with sem:
                    error = None
                    for attempt in range(1, attempts + 1):
                        await wait_turn()
                        try:
                            async with asyncio.timeout(timeout):
                                answer = await model(case["question"])
                        except (TimeoutError, ConnectionError) as e:
                            error = e
                            continue
                        except Exception as e:
                            error = e
                            break
                        score = await loop.run_in_executor(pool, score_answer, answer, case["expected"])
                        scores.append(score)
                        out.append(json.dumps({"id": case["id"], "ok": True, "answer": answer, "score": score, "attempts": attempt}))
                        return
                    failed[0] += 1
                    out.append(json.dumps({"id": case["id"], "ok": False, "error": type(error).__name__, "attempts": attempt}))

            todo = [c for c in cases if c["id"] not in done_ids]
            await asyncio.gather(*(one(c) for c in todo))
            return {"run": len(todo), "skipped": len(cases) - len(todo), "ok": len(scores), "failed": failed[0],
                    "mean_score": round(sum(scores) / len(scores), 3) if scores else 0.0, "elapsed": loop.time() - start}
        """,
        why="""Every lesson of the module has a job here:

        - **Concepts (14.1):** the model calls wait, so they run concurrently on the event loop; the scoring computes, so it goes to a process pool, and Little's law sizes
          the `limit`.
        - **Futures (14.2) and processes (14.3):** `run_in_executor` wraps the pool's future in an awaitable, so CPU work fits into async code without blocking the loop,
          and `score_answer` is top-level so a worker process can receive it by name.
        - **asyncio (14.4):** each case is a coroutine, `gather` runs them all, and records are appended as each finishes, in completion order.
        - **Practice (14.5):** the semaphore caps concurrent calls (the peak was exactly 2), the lock-protected spacing keeps call starts at least 0.25 seconds apart, every
          attempt has a timeout so the hanging case fails after three attempts instead of stalling the run, transient errors are retried and the policy error is not, and
          `done_ids` makes the run resumable.

        Writing one JSON line per finished case means `out` could be a file opened in append mode, so an interrupted run keeps everything it finished, and the next run
        passes the recorded ids as `done_ids`. A production runner adds backoff with jitter between retries, token-based rate limits and cost tracking, but the structure
        stays the same."""),
)

recap(
    "Decide by what the work waits on: computation to processes, waiting to threads or asyncio; then decide what is shared.",
    "Bridge the worlds with `asyncio.run` (sync to async), `asyncio.to_thread` (blocking calls) and `run_in_executor` (process pools).",
    "In asyncio, races happen at `await` points: never await between a check and the action it guards, or hold an `asyncio.Lock` over both.",
    "Compose limits (semaphores, spacing or token buckets), timeouts, retries and queues; give each stage its own concurrency.",
    "Write results as they finish and record what is done, so long jobs are observable and resumable.",
)
