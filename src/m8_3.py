from lesson import *

lesson(
    id="m8-3", num="8.3", title="Caching, retries and timing",
    intro="The decorators every production codebase has: caching with `functools.lru_cache` and how it really works, "
          "time-limited caches, what makes a cache key correct, retry decorators with backoff, why a decorator cannot "
          "enforce a timeout on its own, and measuring latency with percentiles. Applied to embeddings, model calls and "
          "service metrics.",
    desc="`lru_cache`, time-limited caches, cache keys, retry with backoff, and timing decorators.",
    keys="cache lru_cache functools cache cache_info cache_clear maxsize typed hashable key ttl expiry stale memoization retry backoff jitter tenacity timeout perf_counter monotonic latency percentile p95 quantiles embedding cache",
)

term("Memoization", "Remembering the result of a function call for given arguments, so the next identical call returns the stored result instead of recomputing.")
term("LRU cache", "A cache with a size limit that evicts the Least Recently Used entry when it is full.")
term("Cache key", "What a cache uses to decide that two calls are \"the same\". If it leaves out something that changes the result, the cache returns wrong answers.")
term("Percentile", "The value below which a given share of measurements fall. The 95th percentile (p95) latency is the time 95% of calls stay under.")

section("lru", "`functools.lru_cache`: how it works",
    p("""Memoization, which you built by hand in 8.1, is in the standard library: `@functools.lru_cache(maxsize=128)` and its unbounded
    form `@functools.cache`. On each call, the wrapper builds a **key** from the arguments, looks it up in a dict, and returns the
    stored result on a **hit**; on a **miss** it calls the function, stores the result and returns it. With a `maxsize`, the cache
    also tracks the order in which entries were used, and when it is full it evicts the **least recently used** entry, the one
    that has gone longest without a hit. `cache_info()` reports hits, misses and sizes, and `cache_clear()` empties it."""),
    ex("""
    import functools

    calls = []

    @functools.lru_cache(maxsize=2)
    def tokens(text):
        calls.append(text)
        return len(text.split())

    for t in ["refund policy", "reset password", "refund policy", "invoice copy", "reset password"]:
        tokens(t)
    print(calls)
    print(tokens.cache_info())
    tokens.cache_clear()
    print(tokens.cache_info().currsize, tokens.__wrapped__("a b c"))
    """, "lru.py"),
    p("""Follow the calls: two misses fill the cache, the repeated `"refund policy"` is a hit and becomes the most recently used, so when
    `"invoice copy"` arrives, `"reset password"` is the least recently used and is evicted. Asking for it again is therefore a miss
    and it is computed a second time. `lru_cache` uses `functools.wraps`, so `__wrapped__` gives the undecorated function, handy in
    tests that should not touch the cache."""),
    p("""The key rules matter in practice. Every argument must be **hashable**, or the call raises `TypeError: unhashable type: 'list'`
    (problem 3). Positional and keyword forms are **different keys**: `f(1, 2)` and `f(1, b=2)` are cached separately, even
    though they mean the same thing. Equal values of different types are a grey area: the documentation says they are "usually"
    treated as the same call, but CPython has a fast path that uses a single `int` or `str` argument directly as the key, so `f(1)`
    gets its own entry while `f(1.0)` and `f(True)` share one. Never rely on either behaviour; pass `typed=True` when the type of an
    argument matters (problem 16). And the cache stores the **object** returned, so a mutable result such as a list
    is shared by every caller that gets a hit: a caller that appends to it changes the cached value for everyone (problem 4)."""),
)

section("when", "When caching is safe, and what it costs",
    p("""Caching is only correct for functions whose result depends **only on their arguments**: the same arguments must always produce
    the same answer, and calling it must have no side effects that callers rely on. Pure computations (parsing, tokenising,
    formatting, feature extraction) qualify. Functions that read the clock, random numbers, files, databases or the network do not,
    because the world changes while the cache keeps the old answer; caching them is a decision about **staleness**, which a
    time-limited cache makes explicit (below)."""),
    p("""LLM calls sit in between. With temperature 0, a provider usually returns the same answer for the same request, though not
    guaranteed; with temperature above 0, answers vary by design, and caching freezes one sample. Embeddings for a given model are
    deterministic in practice, which is why embedding caches are everywhere: re-embedding an unchanged document costs money and time
    for nothing. In both cases the **key** must include everything that affects the result: the model, the full prompt including the
    system message, and every parameter. A cache keyed only on the user's question returns a cheap model's answer to a request for
    the expensive one (problem 6)."""),
    p("""The costs are memory and correctness. `@functools.cache` never evicts, so a function called with ever-new arguments (request ids,
    timestamps, user texts) grows until the process runs out of memory; give long-running services a `maxsize` (problem 10). A
    cache also keeps every argument and result **alive** (2.1), including large arrays. And a decorated method caches on `self`,
    keeping every instance it has seen alive for as long as the cache exists (Module 9 shows the alternatives)."""),
    callout("sql", "SQL / Power BI", """A cache is a materialised result: Power BI's import mode or a materialised view in SQL stores the
    answer so queries do not recompute it. The same trade-off applies: fast reads, but the result is only as fresh as the last
    refresh, and a refresh policy (a TTL, a schedule, invalidation on change) is part of the design, not an afterthought."""),
)

section("ttl", "Time-limited caches",
    p("""A **TTL** ("time to live") cache stores each entry together with the time it was created, and treats entries older than the TTL
    as missing. It makes staleness a number: "an exchange rate may be up to 60 seconds old", "a retrieved document list may be up to
    10 minutes old". `lru_cache` has no TTL, so it is a common hand-written decorator. Injecting the clock makes it testable without
    waiting (problem 5)."""),
    ex("""
    import functools

    def ttl_cache(seconds, clock):
        def decorator(func):
            store = {}

            @functools.wraps(func)
            def wrapper(*args):
                now = clock()
                if args in store:
                    value, created = store[args]
                    if now - created < seconds:
                        return value
                value = func(*args)
                store[args] = (value, now)
                return value
            wrapper.cache_clear = store.clear
            return wrapper
        return decorator

    now = [0.0]
    fetched = []

    @ttl_cache(seconds=60, clock=lambda: now[0])
    def exchange_rate(currency):
        fetched.append((currency, now[0]))
        return {"EUR": 1.08, "GBP": 1.27}[currency]

    exchange_rate("EUR"); now[0] = 30; exchange_rate("EUR"); now[0] = 61; exchange_rate("EUR")
    print(fetched)
    """, "ttl.py"),
    p("""Expired entries in this simple version stay in memory until they are next requested; production caches also bound their size
    and purge old entries. Libraries such as `cachetools` (`TTLCache`, `LRUCache`) and external stores such as Redis (with per-key
    expiry) provide this, and Redis also lets several processes share one cache, which `lru_cache` cannot."""),
)

section("retry", "Retry as a decorator",
    p("""Lesson 7.4 built the retry logic: transient errors only, exponential backoff with jitter, a maximum number of attempts, and
    re-raising the last error. As a decorator factory it becomes a one-line policy on any function: `@retry(attempts=4,
    on=(TimeoutError, ConnectionError))`. Keep `sleep` and the random generator injectable (with production defaults) so tests can run
    the whole sequence instantly."""),
    ex("""
    import functools, random, time

    def retry(*, attempts=3, on=(TimeoutError, ConnectionError), base=0.5, cap=8.0, sleep=time.sleep, rng=random.Random()):
        if attempts < 1:
            raise ValueError("attempts must be at least 1")

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(1, attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except on:
                        if attempt == attempts:
                            raise
                        sleep(rng.uniform(0, min(cap, base * 2 ** (attempt - 1))))
            return wrapper
        return decorator

    waits = []
    failures = iter([TimeoutError("t1"), ConnectionError("c1")])

    @retry(attempts=3, sleep=waits.append, rng=random.Random(7))
    def ask(q):
        err = next(failures, None)
        if err:
            raise err
        return f"answer: {q}"

    print(ask("refund?"), [round(w, 3) for w in waits])
    """, "retry_decorator.py"),
    p("""The `tenacity` library is the full-featured version: `@retry(stop=stop_after_attempt(4), wait=wait_random_exponential(max=30),
    retry=retry_if_exception_type(TimeoutError))`, plus callbacks before sleeping, statistics, and support for `async` functions. Most
    LLM SDKs already retry internally (the OpenAI and Anthropic clients retry twice by default); adding your own decorator on top
    multiplies the attempts, so decide which layer owns retries."""),
    p("""A word on **timeouts**. A decorator cannot safely stop a synchronous function that is already running: Python has no way to
    interrupt a thread from outside. The Unix-only `signal.alarm` trick works only in the main thread, and running the function in a
    helper thread with a timeout abandons the thread rather than stopping it. So timeouts belong **inside** the I/O call: pass
    `timeout=` to the HTTP client or SDK, which can give up on the network operation itself. With `async` code (14.5),
    `asyncio.timeout()` can cancel a waiting coroutine, which is one of the reasons LLM services are often written with asyncio."""),
)

section("timing", "Timing and latency statistics",
    p("""For measuring durations, use `time.perf_counter()`: a high-resolution clock meant for intervals that never jumps backwards.
    `time.time()` is wall-clock time, which can jump when the system clock is adjusted (NTP corrections, daylight saving changes on
    some systems), producing negative or huge "durations". `time.monotonic()` also never goes backwards and is the right clock for
    timeouts and deadlines."""),
    p("""A single average hides what users feel. Latencies are usually skewed: most calls are fast and a few are very slow, and those
    few are the ones users complain about. Services therefore report **percentiles**: p50 (the median, a typical call), p95 and p99
    (the slow tail). An LLM endpoint with a mean of 1.2 s can have a p99 of 9 s. `statistics.quantiles(data, n=100)` returns the
    99 cut points between percentiles; for small samples, the simple **nearest-rank** method (sort, then take the value at position
    `ceil(p * n)`) is easy to reason about (problem 15)."""),
    ex("""
    import math, statistics

    latencies = [0.8, 0.9, 1.0, 1.1, 0.9, 1.0, 1.2, 0.95, 8.5, 1.05]

    def nearest_rank(data, p):
        ordered = sorted(data)
        return ordered[max(0, math.ceil(p * len(ordered)) - 1)]

    print(round(statistics.mean(latencies), 3), statistics.median(latencies))
    print(nearest_rank(latencies, 0.50), nearest_rank(latencies, 0.95), nearest_rank(latencies, 0.99))
    q = statistics.quantiles(latencies, n=100, method="inclusive")
    print(round(q[49], 3), round(q[94], 3))
    """, "percentiles.py"),
    p("""One slow call (8.5 s) pulls the mean to almost twice the median, while the median still describes a typical call. The p95 and
    p99 by nearest rank both land on the slow call, because with ten samples the top 5% is a single value; percentiles of tiny
    samples are noisy, so dashboards compute them over many calls. `statistics.quantiles` **interpolates** between neighbouring
    values, so its p95 here lands between the second-slowest call and the outlier (5.215 s) rather than on the outlier. Both methods
    are standard; on small samples they can differ a lot, so state the method next to the number."""),
)

section("warmup", "Warm-up",
    predict("Hits, misses and keys", "easy",
        code="""
        import functools

        @functools.lru_cache(maxsize=None)
        def area(w, h=1):
            return w * h

        area(2, 3); area(2, 3); area(2, h=3); area(w=2, h=3)
        print(area.cache_info())
        area(4); area(4.0)
        print(area.cache_info().hits, area.cache_info().currsize)
        print(area(4.0), type(area(4.0)).__name__)
        """,
        hints=["Positional and keyword forms make different keys.", "CPython uses a single `int` argument directly as the key, but wraps a single `float` in a tuple."],
        why="""`area(2, 3)` misses, then hits. `area(2, h=3)` and `area(w=2, h=3)` are two more **different** keys, so two more misses: 1 hit,
        3 misses. `area(4)` and `area(4.0)` are both misses, even though `4 == 4.0`: CPython's fast path stores a lone `int` (or `str`)
        argument as the bare key, while `4.0` gets a tuple key, and the two do not match. So the cache now holds 5 entries, and the
        last line returns the float result `4.0`. The documentation only promises that equal values of different types are "usually"
        treated as the same call, which is why `typed=True` exists."""),
    write("Normalise before the cache", "easy", tag="RAG",
        prompt="""Users type the same question in many forms. Write `search(query)` that normalises the query (strip, lower-case,
        collapse whitespace) and then calls a cached helper `_search(normalised)` decorated with `functools.lru_cache(maxsize=256)`,
        which returns `run_search(normalised)` (given). Equivalent queries must hit the cache.""",
        code="""
        import functools

        searched = []

        def run_search(q):
            searched.append(q)
            return [f"doc for {q}"]

        def search(query):
            pass
        """,
        tests="""
        assert search("Refund  Policy") == ["doc for refund policy"]
        assert search("  refund policy ") == ["doc for refund policy"]
        assert search("REFUND\\tpolicy") == ["doc for refund policy"]
        assert searched == ["refund policy"]
        assert _search.cache_info().hits == 2
        """,
        hints=["Define `@functools.lru_cache(maxsize=256) def _search(q): return run_search(q)`, and in `search`, `\" \".join(query.lower().split())`."],
        solution="""
        import functools

        searched = []

        def run_search(q):
            searched.append(q)
            return [f"doc for {q}"]

        @functools.lru_cache(maxsize=256)
        def _search(q):
            return run_search(q)

        def search(query):
            return _search(" ".join(query.lower().split()))
        """,
        why="""Caching `search` directly would key on the raw text, so three spellings of one question would be three misses. Normalising
        first maps them to one key, which raises the hit rate without changing results, because the search itself only ever sees
        normalised text. Splitting the work into a public function that normalises and a private cached one is a common shape. Note
        that the cached list is shared by all callers (a caller appending to it would change the cache), which is why some code returns
        tuples from cached functions."""),
    fix("Caching a function that receives a list", "easy", tag="GenAI",
        prompt="""`embed_many(texts)` is decorated with `lru_cache`, but callers pass lists, so every call fails with `TypeError:
        unhashable type: 'list'`. Keep the cache, keep the public signature (it takes a list), and make it work.""",
        code="""
        import functools

        calls = []

        @functools.lru_cache(maxsize=128)
        def embed_many(texts):
            calls.append(texts)
            return [[len(t)] for t in texts]
        """,
        tests="""
        assert embed_many(["a", "bb"]) == [[1], [2]]
        assert embed_many(["a", "bb"]) == [[1], [2]]
        assert len(calls) == 1
        assert embed_many(["c"]) == [[1]] and len(calls) == 2
        """,
        hints=["Cache a helper that takes a **tuple**, and convert the list in a thin public function."],
        solution="""
        import functools

        calls = []

        @functools.lru_cache(maxsize=128)
        def _embed_many(texts):
            calls.append(texts)
            return [[len(t)] for t in texts]

        def embed_many(texts):
            return _embed_many(tuple(texts))
        """,
        why="""`lru_cache` builds its key from the arguments, and lists are unhashable because they can change (4.5): a list used as a key
        could be modified after storing, and the cache would never find it again. Converting to a tuple produces an immutable, hashable
        key with the same contents. The public function keeps accepting lists, so callers do not change. For large inputs, a key built
        from a hash of the contents (`hashlib.sha256`) keeps the cache's memory smaller than storing every tuple."""),
    predict("A cached list is shared", "easy",
        code="""
        import functools

        @functools.lru_cache(maxsize=None)
        def stop_words(lang):
            print("loading", lang)
            return ["the", "a"] if lang == "en" else ["der", "die"]

        words = stop_words("en")
        words.append("refund")                  # a caller changes the returned list
        print(stop_words("en"))
        print(stop_words("en") is words, stop_words.cache_info().hits)
        """,
        hints=["A hit returns the stored object itself, not a copy."],
        why="""The list was loaded once. The caller's `append` changed the cached object, so every later caller receives `["the", "a",
        "refund"]`: a bug that appears far from its cause. Every hit returns the very same object, which `is` confirms. Return immutable
        values (a tuple, a `frozenset`) from cached functions, or copy on the way out."""),
)

section("medium", "Medium",
    write("A TTL cache with keyword arguments", "medium", tag="GenAI",
        prompt="""Write a decorator factory `ttl_cache(seconds, clock)` that caches results for `seconds` (an entry created at time `t`
        is valid while `clock() - t < seconds`). The key must combine positional arguments and keyword arguments sorted by name.
        Expose `wrapper.cache_clear()` and `wrapper.stats()` returning `{"hits": h, "misses": m}`. Use `functools.wraps`.""",
        code="""
        import functools

        def ttl_cache(seconds, clock):
            pass
        """,
        tests="""
        now = [0.0]
        fetched = []

        @ttl_cache(10, clock=lambda: now[0])
        def retrieve(query, *, k=3):
            fetched.append((query, k, now[0]))
            return [f"{query}-{i}" for i in range(k)]

        retrieve("refund"); retrieve("refund"); retrieve("refund", k=2)
        now[0] = 9.9
        retrieve("refund")
        now[0] = 10.0
        retrieve("refund")
        assert fetched == [("refund", 3, 0.0), ("refund", 2, 0.0), ("refund", 3, 10.0)]
        assert retrieve.stats() == {"hits": 2, "misses": 3}
        retrieve.cache_clear()
        retrieve("refund")
        assert len(fetched) == 4 and retrieve.__name__ == "retrieve"
        """,
        hints=["Store `key -> (value, created_at)`. On a lookup, a present but expired entry counts as a miss.",
               "Keep the counters in a small dict in the decorator level and return a copy from `stats()`."],
        solution="""
        import functools

        def ttl_cache(seconds, clock):
            def decorator(func):
                store = {}
                counts = {"hits": 0, "misses": 0}

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    key = (args, tuple(sorted(kwargs.items())))
                    now = clock()
                    entry = store.get(key)
                    if entry is not None and now - entry[1] < seconds:
                        counts["hits"] += 1
                        return entry[0]
                    counts["misses"] += 1
                    value = func(*args, **kwargs)
                    store[key] = (value, now)
                    return value

                wrapper.cache_clear = store.clear
                wrapper.stats = lambda: dict(counts)
                return wrapper
            return decorator
        """,
        why="""Each entry carries its creation time, and validity is a comparison with the injected clock, so the test controls time exactly:
        at 9.9 s the entry is still valid, at 10.0 it has expired and is refetched. Sorting keyword items makes the key independent of
        keyword order, and `k=2` is a separate key from the default `k=3` because the parameters genuinely differ. `stats` returns a
        copy so callers cannot alter the counters. The hit rate, `hits / (hits + misses)`, is the number to watch when tuning a TTL:
        longer TTLs raise it at the price of staler answers."""),
    fix("A model cache that ignores the model", "medium", tag="GenAI",
        prompt="""`complete(prompt, model, temperature)` caches answers in `CACHE` keyed by the prompt only, so asking the large model
        returns the small model's cached answer. Fix the key so every argument that affects the answer is part of it. Only
        temperature 0 calls may be cached at all.""",
        code="""
        CACHE = {}
        calls = []

        def call_model(prompt, model, temperature):
            calls.append((prompt, model, temperature))
            return f"{model}@{temperature}: {prompt}"

        def complete(prompt, model="small", temperature=0.0):
            if prompt in CACHE:
                return CACHE[prompt]
            answer = call_model(prompt, model, temperature)
            CACHE[prompt] = answer
            return answer
        """,
        tests="""
        assert complete("Refund?") == "small@0.0: Refund?"
        assert complete("Refund?", model="large") == "large@0.0: Refund?"
        assert complete("Refund?", model="large") == "large@0.0: Refund?"
        a = complete("Write a poem", temperature=0.9)
        b = complete("Write a poem", temperature=0.9)
        assert len(calls) == 4 and len(CACHE) == 2
        """,
        hints=["Key by `(prompt, model, temperature)`, and skip the cache entirely when `temperature != 0`."],
        solution="""
        CACHE = {}
        calls = []

        def call_model(prompt, model, temperature):
            calls.append((prompt, model, temperature))
            return f"{model}@{temperature}: {prompt}"

        def complete(prompt, model="small", temperature=0.0):
            if temperature != 0:
                return call_model(prompt, model, temperature)
            key = (prompt, model, temperature)
            if key not in CACHE:
                CACHE[key] = call_model(prompt, model, temperature)
            return CACHE[key]
        """,
        why="""A cache key must contain **everything** that can change the result; leaving out the model meant two different requests looked
        identical, and the second got the first one's answer, a silent correctness bug. Sampling with a temperature above 0 is meant to
        produce varied answers, so caching it would freeze one sample and defeat the purpose; those calls bypass the cache. In a real
        system the key also includes the system prompt (or its version), tool definitions and every generation parameter, and is
        usually a hash of a canonical JSON encoding of the whole request."""),
    write("A retry decorator", "medium", tag="GenAI",
        prompt="""Write a decorator factory `retry(*, attempts, on, base, sleep, rng)` that retries the function on the exception types in
        `on`, waiting `rng.uniform(0, base * 2 ** (n - 1))` before retry `n`, and re-raises the last error when the attempts are used up.
        Record the number of attempts the last call used in `wrapper.last_attempts`. Raise `ValueError` at creation if `attempts < 1`.
        Use `functools.wraps`.""",
        code="""
        import functools

        def retry(*, attempts, on, base, sleep, rng):
            pass
        """,
        tests="""
        from types import SimpleNamespace
        top = SimpleNamespace(uniform=lambda a, b: b)
        waits = []
        outcomes = iter([TimeoutError(), TimeoutError(), "ok", ConnectionError("down"), KeyError("bug")])

        @retry(attempts=3, on=(TimeoutError, ConnectionError), base=1.0, sleep=waits.append, rng=top)
        def call():
            out = next(outcomes)
            if isinstance(out, Exception):
                raise out
            return out

        assert call() == "ok" and call.last_attempts == 3 and waits == [1.0, 2.0]
        try:
            call()
            assert False
        except KeyError:
            assert call.last_attempts == 2 and waits == [1.0, 2.0, 1.0]
        try:
            retry(attempts=0, on=(TimeoutError,), base=1, sleep=None, rng=top)
            assert False
        except ValueError:
            pass
        assert call.__name__ == "call"
        """,
        hints=["Loop `for attempt in range(1, attempts + 1)`, set `wrapper.last_attempts = attempt` at the start of each attempt."],
        solution="""
        import functools

        def retry(*, attempts, on, base, sleep, rng):
            if attempts < 1:
                raise ValueError("attempts must be at least 1")

            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, attempts + 1):
                        wrapper.last_attempts = attempt
                        try:
                            return func(*args, **kwargs)
                        except on:
                            if attempt == attempts:
                                raise
                            sleep(rng.uniform(0, base * 2 ** (attempt - 1)))
                wrapper.last_attempts = 0
                return wrapper
            return decorator
        """,
        why="""The retry logic of 7.4, packaged so the policy is one line above any function. In the second call, the `ConnectionError` is
        retried (one wait of 1.0), and the `KeyError` on the second attempt is not in `on`, so it propagates immediately, with
        `last_attempts` showing where it stopped. Settings are keyword-only and validated at decoration time. Recording the attempt
        count on the wrapper is a cheap metric: a function that regularly needs three attempts is a sign of an unhealthy dependency long
        before it fails outright."""),
    choose("Recompute or cache", "medium", tag="ML",
        prompt="Both featurise 100,000 texts drawn from 1,000 distinct strings. Which is faster?",
        setup="""import functools, re

WORD = re.compile(r"[a-z]+")

def featurise(text):
    words = WORD.findall(text.lower())
    return (len(words), sum(len(w) for w in words), len(set(words)))

cached_featurise = functools.lru_cache(maxsize=2048)(featurise)
texts = [f"Refund request number {i % 1000} for order {i % 1000} please help" for i in range(100_000)]""",
        options={
            "a": "rows = [featurise(t) for t in texts]",
            "b": "rows = [cached_featurise(t) for t in texts]",
        },
        answer="b",
        hints=["How many times does each version run the regex and the counting?"],
        why="""Version A tokenises every text, 100,000 times. Version B computes each of the 1,000 distinct texts once and answers the other
        99,000 calls with a dict lookup, and a lookup is much cheaper than a regex pass plus counting. The cache only pays off because
        texts repeat; with all-distinct inputs it would add overhead and memory for nothing. Returning a tuple keeps the cached results
        safe from accidental modification by callers."""),
    trace("An LRU cache step by step", "medium",
        prompt="Fill in `hits`, `misses` and `size` after each marked line.",
        code="""
        import functools

        @functools.lru_cache(maxsize=2)
        def f(x):
            return x * 2

        def info():
            i = f.cache_info()
            return i.hits, i.misses, i.currsize

        f(1); f(2)
        hits, misses, size = info()  # row: "f(1), f(2)"
        f(1)
        hits, misses, size = info()  # row: "f(1) again"
        f(3)
        hits, misses, size = info()  # row: "f(3) evicts"
        f(2)
        hits, misses, size = info()  # row: "f(2)"
        f(1); f(3)
        hits, misses, size = info()  # row: "f(1), f(3)"
        """,
        trace_vars=["hits", "misses", "size"],
        hints=["A hit makes an entry the most recently used. When full, the least recently used entry is evicted."],
        why="""1 and 2 are misses. `f(1)` again is a hit, making 1 the most recently used, so `f(3)` evicts 2. `f(2)` is therefore a miss, and
        it evicts the least recently used entry, which is now 1 (3 was used more recently). Then `f(1)` misses again and evicts 3, so
        `f(3)` misses too. The cache never holds more than two entries, so `currsize` stays 2 once full."""),
    fix("A cache that grows forever", "medium", tag="ML",
        prompt="""A long-running scoring service caches `score(request_id, text)`, but every request has a new id, so the cache
        never gets a hit and memory grows without limit. Change the caching so that only the text is part of the key, with at most
        1,000 entries, while `score` keeps its signature and still logs the request id.""",
        code="""
        import functools

        LOG = []

        @functools.cache
        def score(request_id, text):
            LOG.append(request_id)
            return round(len(set(text.split())) / max(1, len(text.split())), 3)
        """,
        tests="""
        a = score("r1", "refund refund policy")
        b = score("r2", "refund refund policy")
        assert a == b == 0.667
        assert LOG == ["r1", "r2"]
        assert _score_text.cache_info().hits == 1 and _score_text.cache_info().maxsize == 1000
        """,
        hints=["Move the computation into `_score_text(text)` with `@functools.lru_cache(maxsize=1000)`; `score` logs and delegates."],
        solution="""
        import functools

        LOG = []

        @functools.lru_cache(maxsize=1000)
        def _score_text(text):
            return round(len(set(text.split())) / max(1, len(text.split())), 3)

        def score(request_id, text):
            LOG.append(request_id)
            return _score_text(text)
        """,
        why="""Two problems in one: the key included an argument (`request_id`) that does not affect the result but is unique per call, so the
        hit rate was zero; and `functools.cache` has no size limit, so every request added an entry forever, a memory leak. The fix
        caches only the pure part, keyed by what actually determines the result, with a bounded LRU cache. A side effect such as
        logging must never be inside a cached function either, because on a hit it would silently not happen; here the log stays in
        the uncached outer function, so every request is still logged."""),
    refactor("A hand-made cache into lru_cache", "medium", tag="Data work",
        prompt="Replace the manual dictionary cache with `functools.lru_cache`, same results and same number of loads. Keep the tests green.",
        code="""
        _SCHEMAS = {}
        loads = []

        def load_schema(name):
            if name in _SCHEMAS:
                return _SCHEMAS[name]
            loads.append(name)
            schema = {"name": name, "fields": tuple(sorted({"id", name + "_id", "created"}))}
            _SCHEMAS[name] = schema
            return schema
        """,
        tests="""
        a = load_schema("orders")
        b = load_schema("orders")
        c = load_schema("users")
        assert a is b and a["fields"] == ("created", "id", "orders_id")
        assert loads == ["orders", "users"]
        """,
        hints=["Decorate with `@functools.lru_cache(maxsize=None)` and remove the dictionary logic."],
        solution="""
        import functools

        loads = []

        @functools.lru_cache(maxsize=None)
        def load_schema(name):
            loads.append(name)
            return {"name": name, "fields": tuple(sorted({"id", name + "_id", "created"}))}
        """,
        why="""The decorator does exactly what the hand-written code did, returning the same object on a hit (so `a is b` still holds), and adds
        `cache_info()`, `cache_clear()` and thread safety for free. The function body now contains only the real work. Note the
        `loads.append`: a side effect in a cached function runs only on misses, which is what this test wants (counting loads), but would
        be a bug if the side effect were something callers rely on every time. `maxsize=None` is equivalent to `functools.cache`;
        unbounded is fine here because the set of schema names is small and fixed."""),
    predict("Latency statistics", "medium",
        code="""
        import math, statistics

        ms = [120, 95, 110, 2400, 105, 130, 98, 102, 115, 99, 101, 97]

        def pct(data, p):
            s = sorted(data)
            return s[max(0, math.ceil(p * len(s)) - 1)]

        print(round(statistics.mean(ms)), statistics.median(ms))
        print(pct(ms, 0.5), pct(ms, 0.9), pct(ms, 0.95), max(ms))
        fast = [x for x in ms if x < 1000]
        print(round(statistics.mean(fast), 1), len(fast))
        """,
        hints=["The median of an even number of values is the mean of the middle two. Nearest rank takes the value at position `ceil(p * n)` (counting from 1)."],
        why="""One 2.4 s outlier lifts the mean to about 298 ms, almost three times the median of 103.5 ms (the mean of 102 and 105). By nearest
        rank with 12 values, p50 is the 6th value (102), p90 the 11th (130) and p95 the 12th, which is the outlier itself: with few
        samples, high percentiles are just the slowest calls. Dropping the outlier gives a mean close to the median, which is why the
        mean alone misleads for latency."""),
)

section("hard", "Hard",
    write("A batch-aware embedding cache", "hard", tag="RAG",
        prompt="""Embedding APIs are called with batches, so a per-call `lru_cache` on the batch is useless. Write
        `make_cached_embedder(embed_batch)` returning `embed(texts)`: it returns one vector per input text, in order (duplicates
        included), sends only texts **not yet cached** to `embed_batch` in **one** call (each distinct text once), and never calls
        `embed_batch` when everything is cached. Expose the cache dict as `embed.cache`.""",
        code="""
        def make_cached_embedder(embed_batch):
            pass
        """,
        tests="""
        sent = []
        def embed_batch(texts):
            sent.append(list(texts))
            return [[len(t), t.count(" ")] for t in texts]

        embed = make_cached_embedder(embed_batch)
        assert embed(["refund policy", "reset", "refund policy"]) == [[13, 1], [5, 0], [13, 1]]
        assert sent == [["refund policy", "reset"]]
        assert embed(["reset", "invoice copy", "reset"]) == [[5, 0], [12, 1], [5, 0]]
        assert sent[-1] == ["invoice copy"]
        assert embed(["reset", "refund policy"]) == [[5, 0], [13, 1]] and len(sent) == 2
        assert embed([]) == [] and len(embed.cache) == 3
        """,
        hints=["Find the missing texts in order without duplicates with `list(dict.fromkeys(t for t in texts if t not in cache))` (4.5).",
               "Call `embed_batch(missing)` once if `missing` is not empty, store `zip(missing, vectors)` in the cache, then build the result from the cache."],
        solution="""
        def make_cached_embedder(embed_batch):
            cache = {}

            def embed(texts):
                missing = list(dict.fromkeys(t for t in texts if t not in cache))
                if missing:
                    vectors = embed_batch(missing)
                    for text, vec in zip(missing, vectors, strict=True):
                        cache[text] = vec
                return [cache[t] for t in texts]

            embed.cache = cache
            return embed
        """,
        why="""A decorator like `lru_cache` keys on the whole argument, so a batch with one new text would be a miss for all of them. Caching per
        **item** and sending only the missing ones keeps the batching benefit (one API call per request) while never paying twice for
        the same text. `dict.fromkeys` removes duplicates inside one batch while keeping order, so `"refund policy"` appearing twice is
        embedded once, and `zip(..., strict=True)` checks the API returned one vector per text. In production the cache key would be a
        hash of the model name and the exact text, stored in a shared store (Redis, a database table) so all workers and future runs
        benefit, and the cache would be invalidated when the embedding model changes, since vectors from different models are not
        comparable."""),
    fix("Read the code: a retry decorator", "hard", tag="GenAI",
        prompt="""This retry decorator is used across a codebase. It should retry only `TimeoutError` and `ConnectionError` by default,
        wait `delay * 2 ** (n - 1)` before retry `n` (never after the last attempt), re-raise the last error if all attempts fail, and
        keep the function's name. Read it, find the bugs and fix them. (`sleep` is injected.)""",
        code="""
        def retry(attempts=3, on=Exception, delay=1.0, sleep=None):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    for i in range(attempts):
                        try:
                            return func(*args, **kwargs)
                        except on:
                            sleep(delay * 2 ** i)
                    return None
                return wrapper
            return decorator
        """,
        tests="""
        waits = []

        def scripted(*outcomes):
            it = iter(outcomes)
            def fn():
                out = next(it)
                if isinstance(out, BaseException):
                    raise out
                return out
            return fn

        f = retry(sleep=waits.append)(scripted(TimeoutError(), "ok"))
        assert f() == "ok" and waits == [1.0]

        waits.clear()
        g = retry(attempts=3, sleep=waits.append)(scripted(TimeoutError("a"), ConnectionError("b"), TimeoutError("c")))
        try:
            g()
            assert False
        except TimeoutError as e:
            assert str(e) == "c" and waits == [1.0, 2.0]

        waits.clear()
        h = retry(sleep=waits.append)(scripted(ValueError("bad input"), "never"))
        try:
            h()
            assert False
        except ValueError:
            assert waits == []

        @retry(sleep=waits.append)
        def named():
            return 1
        assert named.__name__ == "named"
        """,
        hints=["Change the default `on` to `(TimeoutError, ConnectionError)`.",
               "Track the attempt number; on the last one, `raise` instead of sleeping. Delete the `return None`.",
               "Add `functools.wraps(func)`."],
        solution="""
        import functools


        def retry(attempts=3, on=(TimeoutError, ConnectionError), delay=1.0, sleep=None):
            if attempts < 1:
                raise ValueError("attempts must be at least 1")

            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(1, attempts + 1):
                        try:
                            return func(*args, **kwargs)
                        except on:
                            if attempt == attempts:
                                raise
                            sleep(delay * 2 ** (attempt - 1))
                return wrapper
            return decorator
        """,
        why="""Four bugs. **`on=Exception`** as the default retried everything, including `ValueError` for bad input and bugs, so failures were
        delayed by seconds of pointless waiting and repeated calls. **Sleeping after the last attempt** wasted the longest wait of the
        sequence for nothing. **`return None`** after the loop turned "all attempts failed" into a normal-looking `None` result, the
        swallowed-error bug of 7.3; re-raising the last exception on the final attempt fixes both of these at once. And without
        **`functools.wraps`**, every retried function was named `wrapper` in logs and traces. Validating `attempts` up front turns
        `retry(attempts=0)`, which would never call the function at all, into an error at import."""),
    write("Latency percentiles per function", "hard", tag="GenAI",
        prompt="""Write a decorator factory `track_latency(clock, window=1000)` that records the duration of every call (successful or
        not) in a per-function `deque` keeping only the last `window` durations, and exposes `wrapper.latency()` returning `{"count":
        n, "p50": ..., "p95": ..., "max": ...}` computed by nearest rank over the recorded durations (`None` values when there are
        none). Exceptions propagate.""",
        code="""
        import functools, math
        from collections import deque

        def track_latency(clock, window=1000):
            pass
        """,
        tests="""
        ticks = iter([0, 1, 10, 12, 20, 23, 30, 34, 40, 50])
        clock = lambda: next(ticks)

        @track_latency(clock, window=4)
        def ask(fail=False):
            if fail:
                raise TimeoutError("slow")
            return "ok"

        assert ask.latency() == {"count": 0, "p50": None, "p95": None, "max": None}
        ask(); ask(); ask()
        try:
            ask(fail=True)
        except TimeoutError:
            pass
        assert ask.latency() == {"count": 4, "p50": 2, "p95": 4, "max": 4}
        ask()
        assert ask.latency() == {"count": 4, "p50": 3, "p95": 10, "max": 10}
        assert ask.__name__ == "ask"
        """,
        hints=["Record `clock() - start` in a `finally` block, into `deque(maxlen=window)` created in the decorator level.",
               "Nearest rank: `s = sorted(values)`, `s[math.ceil(p * len(s)) - 1]`."],
        solution="""
        import functools, math
        from collections import deque

        def track_latency(clock, window=1000):
            def decorator(func):
                durations = deque(maxlen=window)

                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    start = clock()
                    try:
                        return func(*args, **kwargs)
                    finally:
                        durations.append(clock() - start)

                def latency():
                    if not durations:
                        return {"count": 0, "p50": None, "p95": None, "max": None}
                    s = sorted(durations)
                    rank = lambda p: s[math.ceil(p * len(s)) - 1]
                    return {"count": len(s), "p50": rank(0.50), "p95": rank(0.95), "max": s[-1]}

                wrapper.latency = latency
                return wrapper
            return decorator
        """,
        why="""The durations are 1, 2, 3, 4 for the first four calls (the failed one included, thanks to `finally`), so p50 is the 2nd sorted
        value and p95 the 4th. The fifth call takes 10, and `deque(maxlen=4)` drops the oldest duration (1), so the window becomes 2, 3,
        4, 10: p50 is now 3 and p95 is 10. A bounded window keeps memory constant and makes the statistics describe **recent**
        behaviour, which is what an alert should react to. Failed calls must be included: timeouts are often the slowest calls, and
        excluding them makes a degrading service look healthy. Production systems use histograms (Prometheus, OpenTelemetry) rather than
        raw samples, but the percentiles mean the same thing."""),
    predict("Equal keys, different types", "hard",
        code="""
        import functools

        @functools.lru_cache(maxsize=None)
        def describe(x):
            return f"{x!r} ({type(x).__name__})"

        print(describe(1), "|", describe(1.0), "|", describe(True))

        @functools.lru_cache(maxsize=None, typed=True)
        def describe_typed(x):
            return f"{x!r} ({type(x).__name__})"

        print(describe_typed(1), "|", describe_typed(1.0), "|", describe_typed(True))
        print(describe.cache_info().currsize, describe_typed.cache_info().currsize)

        @functools.lru_cache(maxsize=None)
        def fib(n):
            return n if n < 2 else fib(n - 1) + fib(n - 2)
        print(fib(30), fib.cache_info().misses, fib.cache_info().hits)
        """,
        hints=["A single `int` argument becomes its own key; a `float` or `bool` argument is wrapped in a tuple, and `(1.0,) == (True,)`.",
               "With caching, each `fib(n)` is computed once; recursive calls go through the cached wrapper (8.1)."],
        why="""Without `typed`, `describe(1)` is stored under the bare key `1` (the fast path for a single `int`), so `describe(1.0)` misses and
        stores its own entry under the tuple `(1.0,)`. `describe(True)` uses the tuple `(True,)`, which equals `(1.0,)` and hashes the
        same, so it **hits** the float's entry and prints `1.0 (float)`: the cache answered with a result computed for a different
        type. With `typed=True`, the type is part of every key, so three entries are stored. For `fib(30)`, each value from 0 to 30 is computed once (31 misses), and the recursive calls that
        find an already computed value are hits: 28 of them. Without the cache, `fib(30)` makes about 2.7 million calls."""),
)

section("interview", "Interview questions",
    explain("When is it safe to cache a function's results?", "medium", tag="Interview",
        why="""When the result depends only on the arguments and the function has no side effects that callers rely on: the same arguments
        always give the same answer, and skipping the call changes nothing else. Pure computations qualify. Functions that depend on time,
        randomness, files, databases or the network can be cached only if you accept staleness, made explicit with a TTL or invalidation
        when the source changes. The key must include every input that affects the result: for LLM calls the model, the full prompt
        including system messages, tools and all parameters; sampling with temperature above 0 should usually not be cached. Arguments
        must be hashable, returned mutable objects are shared by all callers, the cache needs a size bound in long-running processes,
        and caches that cross users must not leak one user's data to another."""),
    explain("How does `functools.lru_cache` work, and what are its pitfalls?", "medium", tag="Interview",
        why="""It wraps the function and keeps a dict from a key built from the positional and keyword arguments to the result, plus a doubly
        linked list that records usage order. A hit moves the entry to the most recent end and returns the stored object; a miss calls
        the function, stores the result and, if `maxsize` is exceeded, evicts the least recently used entry. Lookups and updates are
        O(1), it is thread-safe, and `cache_info()` and `cache_clear()` are available. Pitfalls: arguments must be hashable; `f(1, 2)`
        and `f(1, b=2)` are different keys; equal values of different types may or may not share a key unless `typed=True`; the
        returned object is shared, so
        mutating it corrupts the cache; `@cache` (unbounded) leaks memory when arguments keep changing; side effects inside the
        function run only on misses; decorating methods keeps every `self` alive; and the cache is per process, so it does not help
        other workers and disappears on restart."""),
    explain("Design the caching layer for an LLM application.", "hard", tag="Interview",
        why="""Separate the caches by what they store. An **exact response cache** keyed by a hash of the canonical request (model, system prompt
        version, messages, tools, parameters), used only for deterministic requests, with a TTL that reflects how fresh answers must be,
        scoped per tenant or user when responses can contain private data, and stored in a shared store such as Redis so all workers
        benefit. An **embedding cache** keyed by model and text hash, long-lived, and invalidated by model version, which often saves the
        most money in RAG ingestion. A **retrieval cache** for search results with a short TTL, invalidated when the index is updated.
        A **semantic cache** (match similar rather than identical questions via embeddings) can raise the hit rate but risks returning
        an answer to a subtly different question, so it needs a strict similarity threshold and evaluation. Measure hit rate, savings and
        staleness, protect against cache stampedes when a popular entry expires, provider prompt caching (cached prefixes billed at a
        discount) complements but does not replace an application cache, and make it easy to bypass the cache for debugging and
        evaluation runs."""),
)

recap(
    "`functools.lru_cache(maxsize=...)` memoizes by hashable arguments and evicts the least recently used entry; `cache_info()` shows hits and misses.",
    "Cache only results that depend on the arguments alone; the key must include everything that changes the answer (for LLMs: model, full prompt, parameters).",
    "Bound caches in long-running code, never mutate returned objects, keep side effects outside cached functions, and use a TTL when freshness matters.",
    "A retry decorator packages 7.4's policy; a decorator cannot stop a running synchronous call, so pass timeouts to the I/O itself.",
    "Time with `perf_counter`, include failures, and report percentiles (p50, p95, p99), not just the mean.",
)
