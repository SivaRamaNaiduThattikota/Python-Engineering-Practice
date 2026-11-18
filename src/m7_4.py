from lesson import *

lesson(
    id="m7-4", num="7.4", title="Errors in LLM and API code",
    intro="Calls to models and APIs fail in ways local code does not: timeouts, rate limits, overloaded servers, truncated "
          "or refused answers, output that does not parse, and batches where some items fail. How to tell transient from "
          "permanent errors, retry with backoff and jitter within a deadline, repair invalid output, and handle partial "
          "failures, with everything testable through injected clocks and fakes.",
    desc="Timeouts, rate limits, backoff with jitter, deadlines, output repair and partial batch failures.",
    keys="api error timeout rate limit 429 retry-after transient permanent backoff exponential jitter deadline idempotency repair loop finish_reason truncated refusal batch partial failure token bucket circuit request id",
)

term("Transient error", "A failure that may succeed if you try again later: a timeout, a rate limit, a 503. Permanent errors (a bad request, a wrong key) will fail every time.")
term("Exponential backoff", "Waiting longer after each failed attempt, typically doubling: 1 s, 2 s, 4 s, up to a cap.")
term("Jitter", "Randomness added to retry delays so many clients that failed together do not all retry at the same instant.")
term("Idempotent", "An operation that has the same effect whether it runs once or several times, which is what makes it safe to retry.")

section("modes", "How remote calls fail",
    p("""A call to a model API crosses the network to a service you do not control, so it can fail in many more ways than a local
    function. It helps to sort failures by **what you should do about them**, because that, not the exception's name, decides the
    handling code."""),
    html("""<div class="tbl"><table>
      <tr><th>Failure</th><th>Typical signal</th><th>Retry?</th><th>What to do</th></tr>
      <tr><td>Connection failed, reset</td><td><code>ConnectionError</code></td><td>yes</td><td>retry with backoff</td></tr>
      <tr><td>Timed out</td><td><code>TimeoutError</code>, SDK timeout</td><td>yes, carefully</td><td>retry; the request may have been processed</td></tr>
      <tr><td>Rate limited</td><td>HTTP 429, <code>Retry-After</code> header</td><td>yes</td><td>wait at least the given time; slow down</td></tr>
      <tr><td>Server error, overloaded</td><td>HTTP 500, 502, 503, 529</td><td>yes</td><td>retry with backoff; fail over to another provider</td></tr>
      <tr><td>Bad request</td><td>HTTP 400, 404, 422</td><td>no</td><td>fix the request (a bug, or too many tokens)</td></tr>
      <tr><td>Auth or permission</td><td>HTTP 401, 403</td><td>no</td><td>fix the key or account; alert someone</td></tr>
      <tr><td>Truncated answer</td><td><code>finish_reason == "length"</code></td><td>maybe</td><td>raise the token limit, or continue the answer</td></tr>
      <tr><td>Refused or filtered</td><td>a refusal, <code>content_filter</code></td><td>no</td><td>handle as a product case, not an error to retry</td></tr>
      <tr><td>Output does not parse</td><td>your <code>ValueError</code></td><td>yes, with feedback</td><td>ask again with the error (repair)</td></tr>
    </table></div>"""),
    p("""Three of these deserve emphasis. A **timeout** does not mean the request failed on the server: the model may have finished
    and billed you, and only the answer was lost. Retrying is usually fine for reading or generating, but not for operations with
    side effects such as "send this email" unless they are **idempotent** (below). A **rate limit** is the provider telling you how
    to behave, often with the exact wait in the `Retry-After` header; ignoring it gets you limited for longer. And the two
    "successful" failures, truncated and refused answers, arrive with HTTP 200, so no exception is raised unless your code checks
    `finish_reason` or the content and raises one itself (problem 12)."""),
    ex("""
    class APIError(Exception):
        def __init__(self, message, status):
            super().__init__(message)
            self.status = status

    TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504, 529}

    def is_transient(exc):
        if isinstance(exc, (TimeoutError, ConnectionError)):
            return True
        if isinstance(exc, APIError):
            return exc.status in TRANSIENT_STATUS
        return False

    for e in [TimeoutError(), APIError("overloaded", 529), APIError("bad", 400), APIError("key", 401), ValueError("parse")]:
        print(type(e).__name__, getattr(e, "status", "-"), is_transient(e))
    """, "transient.py"),
)

section("backoff", "Retrying: exponential backoff and jitter",
    p("""Retrying immediately after a transient failure usually fails again: the server is still overloaded, the rate limit window
    has not passed. **Exponential backoff** waits longer after each failure, typically doubling from a base delay up to a cap:
    with a base of 1 second and a cap of 30, the waits are 1, 2, 4, 8, 16, 30, 30... seconds. The total wait grows quickly, so a
    few attempts cover a long outage without hammering the service."""),
    p("""Backoff alone has a flaw. When a provider has a hiccup, thousands of clients fail at the same moment, and with identical
    backoff they all retry at exactly 1 s, then exactly 2 s later, in synchronised waves that knock the service over again: the
    **thundering herd**. **Jitter** fixes it by randomising each delay. The widely used "full jitter" scheme picks a random delay
    between 0 and the exponential value, which spreads retries evenly over the window. If the server sends `Retry-After`, wait at
    least that long."""),
    ex("""
    import random

    def delays(attempts, base, cap, rng=None):
        out = []
        for attempt in range(attempts):
            ceiling = min(cap, base * 2 ** attempt)
            out.append(round(rng.uniform(0, ceiling), 2) if rng else ceiling)
        return out

    print(delays(7, base=1, cap=30))
    print(delays(7, base=1, cap=30, rng=random.Random(42)))
    print(sum(delays(7, base=1, cap=30)))
    """, "backoff_schedule.py"),
    p("""Note the seeded `random.Random(42)`: passing the random generator in (instead of calling `random.uniform` directly) makes the
    function reproducible in tests, the same idea as injecting the clock in 7.3's circuit breaker. Real code also injects `sleep`, so
    tests can run a full retry sequence instantly and check the delays that **would** have been waited (problem 5)."""),
    p("""**Idempotency** decides whether a retry is safe. Reading, embedding and generating text are idempotent in effect: doing them
    twice just costs twice. Creating something (a payment, a ticket, a message to a user) is not: a timeout followed by a retry can
    create it twice. APIs solve this with **idempotency keys**: the client generates a unique id per logical operation and sends it
    with every attempt, and the server performs the operation only once per key. Generate the key once, before the first attempt,
    never inside the retry loop."""),
)

section("deadline", "Timeouts and deadlines",
    p("""Every network call needs a **timeout**: without one, a stuck connection can block a worker forever. SDKs accept a timeout
    per request (the OpenAI and Anthropic clients default to 10 minutes, far too long for an interactive feature), and many
    distinguish a **connect** timeout (how long to wait to establish the connection, usually a few seconds) from a **read**
    timeout (how long to wait for the response, which for long generations can legitimately be a minute)."""),
    p("""Retries multiply waiting: three attempts with a 30 s timeout and backoff can keep a user waiting two minutes. So the policy
    that matters to callers is a **deadline**: a total time budget for the whole operation, including all attempts and waits.
    Before each wait, check whether waiting and trying again could still finish before the deadline; if not, give up now and
    raise the last error, instead of sleeping only to fail anyway (problem 6). Pass the remaining time as the timeout of the next
    attempt, so a single slow attempt cannot overrun the budget either."""),
    ex("""
    def plan(deadline, delays, attempt_time):
        # simulate: each attempt takes attempt_time seconds and fails
        now, timeline = 0.0, []
        for delay in delays:
            now += attempt_time
            timeline.append(f"fail@{now:g}")
            if now + delay + attempt_time > deadline:
                timeline.append("give up")
                return timeline
            now += delay
        return timeline

    print(plan(deadline=10, delays=[1, 2, 4, 8], attempt_time=1.5))
    print(plan(deadline=30, delays=[1, 2, 4, 8], attempt_time=1.5))
    """, "deadline.py"),
)

section("output", "When the answer itself is wrong",
    p("""Many failures arrive as a successful response. Check the **finish reason** first: `"stop"` (or `"end_turn"`) means the model
    finished normally; `"length"` (or `"max_tokens"`) means it was cut off at the token limit, so JSON will be incomplete and a
    summary will end mid-sentence; `"content_filter"` or a refusal means the provider or model declined. Treat a truncated answer
    as an error, not as data: raise a specific exception so the caller can raise the limit or ask the model to continue."""),
    p("""Then validate the content. When output must follow a format (JSON with certain fields, one of a few labels), parse it and
    raise `ValueError` (or your own `InvalidOutputError`) when it does not fit. Unlike most errors, this one can often be fixed by
    the model itself: a **repair loop** sends the conversation back with the invalid reply and a short message describing the
    problem ("Your reply was not valid JSON: Expecting ',' delimiter at line 3. Reply with JSON only."), and asks again, for a limited
    number of attempts (problem 7). Structured output features (JSON mode, tool calling with a schema) reduce how often this is
    needed, but do not remove the need to validate."""),
    ex("""
    import json

    class TruncatedError(Exception):
        pass

    class RefusalError(Exception):
        pass

    def content_of(response):
        choice = response["choices"][0]
        reason = choice["finish_reason"]
        if reason == "length":
            raise TruncatedError("answer cut off at the token limit")
        if reason == "content_filter":
            raise RefusalError("answer blocked by the content filter")
        return choice["message"]["content"]

    responses = [
        {"choices": [{"finish_reason": "stop", "message": {"content": '{"label": "spam"}'}}]},
        {"choices": [{"finish_reason": "length", "message": {"content": '{"label": "sp'}}]},
        {"choices": [{"finish_reason": "content_filter", "message": {"content": ""}}]},
    ]
    for r in responses:
        try:
            print(json.loads(content_of(r)))
        except (TruncatedError, RefusalError) as e:
            print(type(e).__name__, "-", e)
    """, "finish_reason.py"),
)

section("batches", "Partial failures in batches",
    p("""When you process many items (embed 10,000 chunks, classify a dataset, call a tool for each search result), some will fail
    while others succeed. The rule is to **keep every success**, record every failure with its item and reason, and decide
    separately what to do with the failures: retry the transient ones in a later round (with backoff between rounds), report
    the permanent ones, and abort only if the failure rate shows a systemic problem (the error budget of 7.3)."""),
    p("""Batch APIs add a twist: one call sends many items, and a single bad item (an empty string, a text over the token limit) can
    make the **whole call** fail with a 400. Retrying the batch is pointless. The usual remedy is to split: retry the batch in
    halves, or item by item, which isolates the bad items and saves the good ones (problem 9). Keep results keyed by item id, not
    by position, so retries and reordering cannot misalign them."""),
    ex("""
    def embed_batch(texts):
        if any(not t.strip() for t in texts):
            raise ValueError("400: input contains an empty string")
        return [[len(t)] for t in texts]

    def embed_all(items):
        vectors, failed = {}, {}
        try:
            for (item_id, _), vec in zip(items, embed_batch([t for _, t in items]), strict=True):
                vectors[item_id] = vec
        except ValueError:
            for item_id, text in items:              # isolate the bad items
                try:
                    vectors[item_id] = embed_batch([text])[0]
                except ValueError as e:
                    failed[item_id] = str(e)
        return vectors, failed

    print(embed_all([("a", "refund"), ("b", "reset")]))
    print(embed_all([("a", "refund"), ("b", "  "), ("c", "invoice")]))
    """, "split_batch.py"),
)

section("observe", "Errors you can debug later",
    p("""API failures are often intermittent, so you debug them from logs long after they happened. For every failed call, record
    the **error type** and status, the provider's **request id** (support teams need it), the **attempt number**, the **latency**,
    the model name, and token counts if available. Do **not** log API keys, and be careful with prompts and outputs, which may
    contain personal data: log their length or a hash, or redact them (5.5), unless you have a policy that allows storing them."""),
    p("""Keep two messages apart: the **internal** one, with every detail, goes to logs; the **user-facing** one says what happened in
    plain words and what the user can do ("The assistant is busy, please try again in a minute"), never a traceback or a provider's
    raw error. And count failures by type in metrics, so a rising rate limit or timeout rate is visible on a dashboard before users
    complain."""),
    ex("""
    import json, time

    def log_failure(log, *, exc, attempt, started, model, request_id=None, prompt=""):
        log.append(json.dumps({
            "event": "llm_call_failed",
            "error": type(exc).__name__,
            "status": getattr(exc, "status", None),
            "attempt": attempt,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "model": model,
            "request_id": request_id,
            "prompt_chars": len(prompt),            # size, not content
        }))

    log = []
    start = time.perf_counter()
    log_failure(log, exc=TimeoutError("read timed out"), attempt=2, started=start, model="small",
                request_id="req_123", prompt="My card number is 4111 1111 1111 1111")
    entry = json.loads(log[0])
    print(sorted(entry), entry["prompt_chars"], "4111" in log[0])
    """, "structured_log.py"),
)

section("warmup", "Warm-up",
    predict("Transient or permanent", "easy",
        code="""
        class APIError(Exception):
            def __init__(self, status):
                super().__init__(f"HTTP {status}")
                self.status = status

        def action(exc):
            if isinstance(exc, (TimeoutError, ConnectionError)):
                return "retry"
            if isinstance(exc, APIError):
                if exc.status == 429 or exc.status >= 500:
                    return "retry"
                if exc.status in (401, 403):
                    return "alert"
                return "fix request"
            return "bug"

        print([action(e) for e in [ConnectionResetError(), APIError(503), APIError(400), APIError(403)]])
        print(action(APIError(429)), action(KeyError("x")), action(TimeoutError()), str(APIError(404)))
        """,
        hints=["`ConnectionResetError` is a subclass of `ConnectionError`."],
        why="""`ConnectionResetError` is a `ConnectionError`, so it is retried. A 503 is a server error, retried; a 400 needs the request
        fixed; a 403 is a permissions problem a human must look at. Rate limits are retried. A `KeyError` is not an API failure at
        all, so it is classified as a bug and should propagate. Classifying by **reaction** keeps the retry code simple: it asks one
        question, "is this worth retrying?"."""),
    write("A backoff schedule", "easy", tag="GenAI",
        prompt="""Write `backoff(attempts, base, cap)` returning the list of waits before each retry: `base`, `2 * base`, `4 *
        base`, ... (`attempts` values), each capped at `cap`. Raise `ValueError` if `base` or `cap` is not positive or `attempts`
        is negative.""",
        code="""
        def backoff(attempts, base, cap):
            pass
        """,
        tests="""
        assert backoff(5, 1, 30) == [1, 2, 4, 8, 16]
        assert backoff(7, 0.5, 4) == [0.5, 1.0, 2.0, 4, 4, 4, 4]
        assert backoff(0, 1, 10) == []
        for bad in [(3, 0, 10), (3, 1, -1), (-1, 1, 10)]:
            try:
                backoff(*bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["`min(cap, base * 2 ** i)` for `i` in `range(attempts)`."],
        solution="""
        def backoff(attempts, base, cap):
            if base <= 0 or cap <= 0 or attempts < 0:
                raise ValueError("base and cap must be positive, attempts non-negative")
            return [min(cap, base * 2 ** i) for i in range(attempts)]
        """,
        why="""The doubling comes from `2 ** i`, and the cap keeps late waits bounded, which is why the second schedule flattens at 4.
        Note the mix of `1.0` and `4`: `min` returns whichever argument is smaller, unchanged, so the result is the float product or the
        integer cap; equality still works because `4 == 4.0`. Production code adds jitter on top of this ceiling (problem 5), and
        validates its configuration up front so a zero base does not turn into a tight retry loop."""),
    fix("Retries that stop one attempt early", "easy", tag="GenAI",
        prompt="""`call(fn, max_retries)` should make **one first attempt plus up to `max_retries` retries** when `fn` raises
        `TimeoutError`, and re-raise the last timeout if all fail. It gives up one attempt too early, and with `max_retries=0` it
        never calls `fn` at all. Fix it.""",
        code="""
        def call(fn, max_retries):
            last = None
            for attempt in range(max_retries):
                try:
                    return fn()
                except TimeoutError as e:
                    last = e
            raise last
        """,
        tests="""
        def flaky(fail_times):
            state = {"n": 0}
            def fn():
                state["n"] += 1
                if state["n"] <= fail_times:
                    raise TimeoutError(f"t{state['n']}")
                return state["n"]
            return fn, state

        fn, state = flaky(2)
        assert call(fn, max_retries=2) == 3 and state["n"] == 3
        fn, state = flaky(0)
        assert call(fn, max_retries=0) == 1
        fn, state = flaky(5)
        try:
            call(fn, max_retries=1)
            assert False
        except TimeoutError as e:
            assert str(e) == "t2" and state["n"] == 2
        """,
        hints=["The number of attempts is `max_retries + 1`."],
        solution="""
        def call(fn, max_retries):
            last = None
            for attempt in range(max_retries + 1):
                try:
                    return fn()
                except TimeoutError as e:
                    last = e
            raise last
        """,
        why=""""Retries" counts the attempts **after** the first, so the loop must run `max_retries + 1` times. With `range(max_retries)`,
        `max_retries=0` meant zero attempts, and the final `raise last` then raised `None`, which is itself a `TypeError: exceptions must
        derive from BaseException`, a confusing error that hides the real problem. Naming parameters precisely (`max_attempts` versus
        `max_retries`) prevents this whole class of bug; SDKs use `max_retries` meaning retries after the first call."""),
    predict("Reading Retry-After", "easy",
        code="""
        def wait_for(headers, default=1.0, cap=60.0):
            raw = headers.get("retry-after")
            try:
                value = float(raw)
            except (TypeError, ValueError):
                return default
            return min(max(value, 0.0), cap)

        print(wait_for({"retry-after": "2"}), wait_for({}), wait_for({"retry-after": "soon"}))
        print(wait_for({"retry-after": "-5"}), wait_for({"retry-after": "3600"}), wait_for({"retry-after": " 0.5 "}))
        """,
        hints=["`float(None)` raises `TypeError`; `float(\"soon\")` raises `ValueError`; `float(\" 0.5 \")` accepts spaces."],
        why="""A missing header gives `None`, and `float(None)` raises `TypeError`; a non-numeric value raises `ValueError`; both fall back to
        the default. The clamping keeps a negative value from becoming a negative sleep (which raises `ValueError` in `time.sleep`) and
        a huge value from blocking a worker for an hour. Real headers can also be an HTTP date, which this simple reader treats as
        invalid and replaces with the default; `email.utils.parsedate_to_datetime` can parse that form."""),
)

section("medium", "Medium",
    write("Retry with full jitter and Retry-After", "medium", tag="GenAI",
        prompt="""Write `retry(fn, max_attempts, sleep, rng, base=1.0, cap=30.0)` that calls `fn()` and retries on `TimeoutError`,
        `ConnectionError` and `RateLimitError` (defined for you, with a `retry_after` attribute that may be `None`). Before retry
        number `n` (from 1), wait `rng.uniform(0, min(cap, base * 2 ** (n - 1)))`, or the rate limit's `retry_after` if that is
        larger, by calling `sleep(seconds)`. Re-raise the last error when attempts run out; let other exceptions propagate. Return
        the result.""",
        code="""
        class RateLimitError(Exception):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after


        def retry(fn, max_attempts, sleep, rng, base=1.0, cap=30.0):
            pass
        """,
        tests="""
        from types import SimpleNamespace
        top = SimpleNamespace(uniform=lambda a, b: b)          # always the ceiling, to make delays predictable

        def scripted(*outcomes):
            it = iter(outcomes)
            def fn():
                out = next(it)
                if isinstance(out, Exception):
                    raise out
                return out
            return fn

        waits = []
        assert retry(scripted(TimeoutError(), ConnectionError(), "ok"), 5, waits.append, top) == "ok"
        assert waits == [1.0, 2.0]
        waits = []
        assert retry(scripted(RateLimitError("429", retry_after=7.5), "ok"), 3, waits.append, top) == "ok" and waits == [7.5]
        waits = []
        try:
            retry(scripted(TimeoutError("a"), TimeoutError("b"), TimeoutError("c")), 3, waits.append, top, base=10, cap=15)
            assert False
        except TimeoutError as e:
            assert str(e) == "c" and waits == [10, 15]
        waits = []
        try:
            retry(scripted(KeyError("bug"), "never"), 3, waits.append, top)
            assert False
        except KeyError:
            assert waits == []
        """,
        hints=["Loop `for attempt in range(1, max_attempts + 1)`; on a retryable error, if `attempt == max_attempts` re-raise, else compute the delay and `sleep(delay)`.",
               "`getattr(e, \"retry_after\", None) or 0` gives the server's wait for any of the three types."],
        solution="""
        class RateLimitError(Exception):
            def __init__(self, message, retry_after=None):
                super().__init__(message)
                self.retry_after = retry_after


        RETRYABLE = (TimeoutError, ConnectionError, RateLimitError)


        def retry(fn, max_attempts, sleep, rng, base=1.0, cap=30.0):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn()
                except RETRYABLE as e:
                    if attempt == max_attempts:
                        raise
                    delay = rng.uniform(0, min(cap, base * 2 ** (attempt - 1)))
                    server_wait = getattr(e, "retry_after", None) or 0
                    sleep(max(delay, server_wait))
        """,
        why="""Injecting `sleep` and `rng` is what makes this testable: the test passes `waits.append` as `sleep`, so the whole retry
        sequence runs instantly and the delays can be checked, and an `rng` whose `uniform` always returns the upper bound turns the
        random jitter into predictable numbers. In production you pass `time.sleep` and `random.Random()`. The server's `Retry-After`
        wins when it is longer than our own backoff, because the provider knows its rate-limit window. A bare `raise` on the last
        attempt preserves the final error. No wait happens after the last failure, since there is no next attempt to wait for. The
        `tenacity` library offers all of this as configurable decorators (8.3)."""),
    fix("Retries that ignore the deadline", "medium", tag="GenAI",
        prompt="""`call_within(fn, deadline, delays, clock, sleep)` retries `fn` on `TimeoutError`, waiting `delays[i]` before retry
        `i + 1`. It must never **start** a wait that would end after `deadline` seconds from the start (measured with `clock()`):
        in that case it re-raises the last timeout immediately. It currently sleeps through every delay regardless. Fix it.""",
        code="""
        def call_within(fn, deadline, delays, clock, sleep):
            start = clock()
            for delay in delays:
                try:
                    return fn()
                except TimeoutError:
                    sleep(delay)
            return fn()
        """,
        tests="""
        now = [0.0]
        clock = lambda: now[0]
        def sleep(s):
            now[0] += s
        def always_slow():
            now[0] += 2.0                   # each attempt takes 2 seconds and times out
            raise TimeoutError(f"at {now[0]}")

        try:
            call_within(always_slow, 10, [1, 2, 4, 8], clock, sleep)
            assert False
        except TimeoutError as e:
            assert str(e) == "at 9.0" and now[0] == 9.0
        now[0] = 0.0
        results = iter([TimeoutError("x"), "ok"])
        def second_works():
            r = next(results)
            if isinstance(r, Exception):
                raise r
            return r
        assert call_within(second_works, 10, [1, 2], clock, sleep) == "ok" and now[0] == 1.0
        now[0] = 0.0
        assert call_within(lambda: "first", 5, [1], clock, sleep) == "first" and now[0] == 0.0
        """,
        hints=["Before sleeping, compute `elapsed = clock() - start`; if `elapsed + delay > deadline`, re-raise with a bare `raise`.",
               "Keep the final attempt after the loop: once the delays are used up, one more try is allowed."],
        solution="""
        def call_within(fn, deadline, delays, clock, sleep):
            start = clock()
            for delay in delays:
                try:
                    return fn()
                except TimeoutError:
                    if clock() - start + delay > deadline:
                        raise
                    sleep(delay)
            return fn()
        """,
        why="""Trace the first test. Attempt 1 fails at 2 s; a 1 s wait would end at 3, within the 10 s deadline, so it waits. Attempt 2
        fails at 5 s; 5 + 2 = 7 still fits, so it waits again. Attempt 3 fails at 9 s, and a 4 s wait would end at 13, past the deadline,
        so it gives up immediately and re-raises the timeout from 9 s, instead of sleeping and trying again. The original slept
        through every delay and only stopped after the fifth attempt, at 25 s, two and a half times the budget. The check uses the
        clock **at the moment of failure**, because attempts take variable time. A complete version would also pass the remaining
        time, `deadline - (clock() - start)`, as the timeout of each attempt, so that one slow attempt cannot overrun the budget on its
        own."""),
    write("Repair invalid output", "medium", tag="GenAI",
        prompt="""Write `ask_json(ask, messages, required, max_attempts)`. `ask(messages)` returns the model's reply text. Parse the
        reply as a JSON object that must contain every key in `required`. If parsing or the check fails, append the reply as an
        assistant message and a user message `"Your reply was invalid: <error>. Reply with only a JSON object with keys: <keys>."`
        (keys comma-separated, in the given order), then ask again. Return `(data, attempts)`. After `max_attempts` failures, raise
        `ValueError("no valid JSON after N attempts")` chained from the last error. Do not modify the caller's `messages` list.""",
        code="""
        import json

        def ask_json(ask, messages, required, max_attempts):
            pass
        """,
        tests="""
        replies = iter(['Sure! {"label": spam}', '{"label": "spam"}', '{"label": "spam", "confidence": 0.9}'])
        seen = []
        def ask(msgs):
            seen.append([m["content"] for m in msgs])
            return next(replies)

        original = [{"role": "user", "content": "Classify: win a prize"}]
        data, attempts = ask_json(ask, original, ["label", "confidence"], 4)
        assert data == {"label": "spam", "confidence": 0.9} and attempts == 3
        assert original == [{"role": "user", "content": "Classify: win a prize"}]
        assert seen[1][1] == 'Sure! {"label": spam}' and seen[1][2].startswith("Your reply was invalid: ")
        assert seen[2][-1] == "Your reply was invalid: missing keys: confidence. Reply with only a JSON object with keys: label, confidence."

        try:
            ask_json(lambda m: "nope", original, ["label"], 2)
            assert False
        except ValueError as e:
            assert str(e) == "no valid JSON after 2 attempts" and isinstance(e.__cause__, ValueError)
        """,
        hints=["Copy first: `history = list(messages)`. Parse with `json.loads`, check `isinstance(data, dict)`, and compute missing keys.",
               "Raise `ValueError(f\"missing keys: ...\")` inside the `try` so one handler covers parse and check errors."],
        solution="""
        import json

        def ask_json(ask, messages, required, max_attempts):
            history = list(messages)
            last_error = None
            for attempt in range(1, max_attempts + 1):
                reply = ask(history)
                try:
                    data = json.loads(reply)
                    if not isinstance(data, dict):
                        raise ValueError("reply is not a JSON object")
                    missing = [k for k in required if k not in data]
                    if missing:
                        raise ValueError(f"missing keys: {', '.join(missing)}")
                    return data, attempt
                except ValueError as e:
                    last_error = e
                    history = history + [
                        {"role": "assistant", "content": reply},
                        {"role": "user", "content": f"Your reply was invalid: {e}. Reply with only a JSON object with keys: {', '.join(required)}."},
                    ]
            raise ValueError(f"no valid JSON after {max_attempts} attempts") from last_error
        """,
        why="""Showing the model its own invalid reply and the precise error ("Expecting value", "missing keys: confidence") usually fixes
        the output on the next try, which is far more effective than asking the identical question again. `json.JSONDecodeError` is a
        `ValueError`, so parse errors and the hand-written checks share one handler. The history is copied and extended with `+`, so
        the caller's list is never modified and a retry from outside starts clean (2.4). The final error is chained from the last
        specific failure, so logs show why the model kept failing. Libraries such as Instructor implement this loop on top of Pydantic
        validation errors (11.4)."""),
    trace("A retry schedule step by step", "medium",
        prompt="Fill in `delay` and `total` after each marked line.",
        code="""
        def ceiling(attempt, base=0.5, cap=4.0):
            return min(cap, base * 2 ** (attempt - 1))

        total = 0.0
        delay = ceiling(1)
        total += delay  # row: "before retry 1"
        delay = ceiling(2)
        total += delay  # row: "before retry 2"
        delay = max(ceiling(3), 5.0)
        total += delay  # row: "retry 3, Retry-After 5"
        delay = ceiling(6)
        total += delay  # row: "before retry 6"
        """,
        trace_vars=["delay", "total"],
        hints=["The ceiling doubles from 0.5 and stops at 4.0. A larger Retry-After replaces the computed wait."],
        why="""The waits are 0.5 and 1.0 for the first two retries. For the third, the computed ceiling is 2.0, but the server asked for
        5 seconds, which wins. By retry 6 the doubling (0.5 x 32 = 16) has passed the cap, so the wait is 4.0. The running total shows
        how quickly backoff adds up, which is why a deadline (problem 6) is needed alongside it."""),
    fix("One bad text fails the whole batch", "medium", tag="RAG",
        prompt="""`embed_documents(docs, embed_batch)` sends all texts in one call. When the API rejects the batch with
        `BadInputError` because of one bad text, nothing is returned. Make it isolate the failures: on `BadInputError`, embed each
        text on its own, keep the successes, and report the failed ids with the error message. Other errors must propagate.""",
        code="""
        class BadInputError(Exception):
            pass


        def embed_documents(docs, embed_batch):
            texts = [d["text"] for d in docs]
            vectors = embed_batch(texts)
            return {d["id"]: v for d, v in zip(docs, vectors)}, {}
        """,
        tests="""
        calls = []
        def embed_batch(texts):
            calls.append(len(texts))
            for t in texts:
                if not t.strip():
                    raise BadInputError("empty input")
                if len(t) > 20:
                    raise BadInputError("input too long")
            return [[len(t)] for t in texts]

        docs = [{"id": "a", "text": "refund"}, {"id": "b", "text": " "}, {"id": "c", "text": "x" * 30}, {"id": "d", "text": "reset"}]
        vectors, failed = embed_documents(docs, embed_batch)
        assert vectors == {"a": [6], "d": [5]} and failed == {"b": "empty input", "c": "input too long"}
        assert calls == [4, 1, 1, 1, 1]
        calls.clear()
        assert embed_documents(docs[:1], embed_batch) == ({"a": [6]}, {}) and calls == [1]
        """,
        hints=["Try the whole batch first. In `except BadInputError:`, loop over the documents and call `embed_batch([text])` for each in its own `try`."],
        solution="""
        class BadInputError(Exception):
            pass


        def embed_documents(docs, embed_batch):
            try:
                vectors = embed_batch([d["text"] for d in docs])
            except BadInputError:
                pass
            else:
                return {d["id"]: v for d, v in zip(docs, vectors, strict=True)}, {}
            good, failed = {}, {}
            for d in docs:
                try:
                    good[d["id"]] = embed_batch([d["text"]])[0]
                except BadInputError as e:
                    failed[d["id"]] = str(e)
            return good, failed
        """,
        why="""Batch calls are cheaper and faster, so the batch is tried first; only when it is rejected does the function pay for one call
        per item, which pinpoints exactly which inputs are bad and saves the rest. Results are keyed by document id, so nothing can be
        misaligned, and `zip(..., strict=True)` checks that the API returned one vector per text. For large batches, splitting in halves
        recursively finds the bad items with far fewer calls than going one by one. Better still, validate cheaply before sending
        (empty strings, length limits), which is the LBYL half of 7.3: check what you can, and handle what you cannot predict."""),
    write("Classify errors for the retry policy", "medium", tag="GenAI",
        prompt="""Write `policy(exc)` returning one of `"retry"`, `"shrink"`, `"alert"` or `"raise"`, for an `APIError(message,
        status)` (defined for you) or any other exception: timeouts and connection errors, and API statuses 408, 409, 429 and 5xx,
        `"retry"`; a 400 whose message mentions the context length (`"context_length"` or `"maximum context"`, any case)
        `"shrink"` (the caller should shorten the prompt); 401 and 403 `"alert"`; anything else `"raise"`.""",
        code="""
        class APIError(Exception):
            def __init__(self, message, status):
                super().__init__(message)
                self.status = status


        def policy(exc):
            pass
        """,
        tests="""
        assert [policy(e) for e in [TimeoutError(), ConnectionResetError(), APIError("busy", 529), APIError("x", 409)]] == ["retry"] * 4
        assert policy(APIError("This model's maximum context length is 8192 tokens", 400)) == "shrink"
        assert policy(APIError("error code: context_length_exceeded", 400)) == "shrink"
        assert policy(APIError("invalid parameter: temperature", 400)) == "raise"
        assert policy(APIError("bad key", 401)) == "alert" and policy(APIError("forbidden", 403)) == "alert"
        assert policy(KeyError("bug")) == "raise" and policy(APIError("not found", 404)) == "raise"
        """,
        hints=["Check the built-in types first, then `isinstance(exc, APIError)` and its `status`. Lower-case the message once for the context check."],
        solution="""
        class APIError(Exception):
            def __init__(self, message, status):
                super().__init__(message)
                self.status = status


        RETRY_STATUS = {408, 409, 429}
        CONTEXT_HINTS = ("context_length", "maximum context")


        def policy(exc):
            if isinstance(exc, (TimeoutError, ConnectionError)):
                return "retry"
            if not isinstance(exc, APIError):
                return "raise"
            if exc.status in RETRY_STATUS or exc.status >= 500:
                return "retry"
            if exc.status == 400 and any(h in str(exc).lower() for h in CONTEXT_HINTS):
                return "shrink"
            if exc.status in (401, 403):
                return "alert"
            return "raise"
        """,
        why="""Putting the classification in one function keeps every retry loop, fallback and alert consistent, and makes the policy easy
        to test exhaustively. The context-length case shows why status codes alone are not enough: it is a 400, like any invalid
        request, but it has a specific remedy (trim the conversation, drop retrieved chunks, or summarise history), so it gets its own
        action. Matching on message text is fragile, which is why the check uses a few known phrasings and the SDKs increasingly expose
        error codes (`context_length_exceeded`) as attributes; prefer those when available. 409 (conflict) is included because some
        APIs use it for transient concurrency conflicts."""),
    refactor("Copy-pasted provider fallbacks", "medium", tag="GenAI",
        prompt="Remove the duplication with a loop over providers. Same results and same `tried` list. Keep the tests green.",
        code="""
        def complete(prompt, providers, tried):
            try:
                tried.append("primary")
                return providers["primary"](prompt)
            except (TimeoutError, ConnectionError):
                pass
            try:
                tried.append("secondary")
                return providers["secondary"](prompt)
            except (TimeoutError, ConnectionError):
                pass
            try:
                tried.append("local")
                return providers["local"](prompt)
            except (TimeoutError, ConnectionError) as e:
                raise RuntimeError("all providers failed") from e
        """,
        tests="""
        def up(name):
            return lambda p: f"{name}: {p}"
        def down(p):
            raise TimeoutError("slow")
        tried = []
        assert complete("hi", {"primary": down, "secondary": up("b"), "local": up("c")}, tried) == "b: hi" and tried == ["primary", "secondary"]
        tried = []
        try:
            complete("hi", {"primary": down, "secondary": down, "local": down}, tried)
            assert False
        except RuntimeError as e:
            assert isinstance(e.__cause__, TimeoutError) and tried == ["primary", "secondary", "local"]
        tried = []
        assert complete("hi", {"primary": up("a"), "secondary": down, "local": down}, tried) == "a: hi" and tried == ["primary"]
        """,
        hints=["Loop over `(\"primary\", \"secondary\", \"local\")`, keep the last error, and raise after the loop."],
        solution="""
        ORDER = ("primary", "secondary", "local")

        def complete(prompt, providers, tried):
            last_error = None
            for name in ORDER:
                tried.append(name)
                try:
                    return providers[name](prompt)
                except (TimeoutError, ConnectionError) as e:
                    last_error = e
            raise RuntimeError("all providers failed") from last_error
        """,
        why="""The three blocks differed only in the provider name, so a loop over an ordered tuple expresses the policy directly: "try each in
        order, move on only on transient failures". Adding a fourth provider is now one word. The last error is kept in a separate
        variable because the `as` name is deleted after each handler, and it becomes the cause of the final `RuntimeError`. Bugs
        (any other exception) still propagate from the first provider that has them. LLM gateways such as LiteLLM implement the same
        ordered fallback, usually combined with a circuit breaker per provider (7.3)."""),
    predict("Handling finish reasons", "medium",
        code="""
        def handle(choice):
            reason = choice.get("finish_reason")
            if reason in ("stop", "end_turn"):
                return choice["text"]
            if reason in ("length", "max_tokens"):
                return choice["text"] + " [truncated]"
            if reason == "tool_calls":
                return "call " + choice["tool"]
            raise ValueError(f"unexpected finish_reason {reason!r}")

        print(handle({"finish_reason": "stop", "text": "Done."}))
        print(handle({"finish_reason": "max_tokens", "text": "The refund policy says"}))
        print(handle({"finish_reason": "tool_calls", "text": "", "tool": "search"}))
        for c in [{"finish_reason": "content_filter", "text": ""}, {"text": "?"}]:
            try:
                handle(c)
            except ValueError as e:
                print(e)
        """,
        hints=["Different providers name the same finish reasons differently. Unknown values should fail loudly."],
        why="""Normal completions return the text. A truncated one is marked here (real code would raise or continue the answer, but must
        never pass it off as complete). A tool call is a request to run a tool, not an answer. The last branch matters most: an
        unknown reason, or a missing one, raises instead of being treated as success, so a new provider behaviour or a filtered answer
        is noticed instead of silently returning an empty string."""),
)

section("hard", "Hard",
    write("Retry failures in rounds", "hard", tag="ML",
        prompt="""Write `run_batch(items, call, max_rounds, on_round=None)` for a dict of `id -> input`. Round 1 calls
        `call(input)` for every item. Items that raise `TimeoutError` are retried in the next round, up to `max_rounds` rounds;
        items that raise `ValueError` fail permanently at once. Before each round after the first, call `on_round(round_number,
        pending_ids)` if given (where backoff would go). Return `(results, failures)`: results maps id to output; failures maps id to
        the exception type name (`"TimeoutError"` for items still timing out after the last round). Other exceptions propagate.""",
        code="""
        def run_batch(items, call, max_rounds, on_round=None):
            pass
        """,
        tests="""
        attempts = {}
        plan = {"a": ["ok"], "b": ["timeout", "ok"], "c": ["bad"], "d": ["timeout", "timeout", "timeout"], "e": ["timeout", "timeout", "ok"]}
        def call(x):
            attempts[x] = attempts.get(x, 0) + 1
            step = plan[x][attempts[x] - 1]
            if step == "timeout":
                raise TimeoutError(x)
            if step == "bad":
                raise ValueError(x)
            return x.upper()

        rounds = []
        results, failures = run_batch({k: k for k in plan}, call, 3, lambda n, ids: rounds.append((n, ids)))
        assert results == {"a": "A", "b": "B", "e": "E"} and failures == {"c": "ValueError", "d": "TimeoutError"}
        assert rounds == [(2, ["b", "d", "e"]), (3, ["d", "e"])]
        assert attempts == {"a": 1, "b": 2, "c": 1, "d": 3, "e": 3}
        assert run_batch({}, call, 3) == ({}, {})
        """,
        hints=["Keep `pending` as a list of ids. Each round builds the next `pending` from the items that timed out.",
               "After the last round, everything still pending is a `TimeoutError` failure."],
        solution="""
        def run_batch(items, call, max_rounds, on_round=None):
            results, failures = {}, {}
            pending = list(items)
            for round_number in range(1, max_rounds + 1):
                if not pending:
                    break
                if round_number > 1 and on_round is not None:
                    on_round(round_number, list(pending))
                still_pending = []
                for item_id in pending:
                    try:
                        results[item_id] = call(items[item_id])
                    except TimeoutError:
                        still_pending.append(item_id)
                    except ValueError as e:
                        failures[item_id] = type(e).__name__
                pending = still_pending
            for item_id in pending:
                failures[item_id] = "TimeoutError"
            return results, failures
        """,
        why="""Retrying in **rounds** instead of retrying each item immediately has two advantages for batch work: one slow item does not
        hold up the rest, and the wait between rounds (via `on_round`, where a real job sleeps with backoff) gives an overloaded service
        time to recover before the stragglers are retried together. Permanent failures are recorded on first sight and never retried.
        Iterating over ids in insertion order keeps rounds deterministic, which the `rounds` check depends on. Every item ends up in
        exactly one of the two dicts, which is the property a batch report needs: processed = succeeded + failed."""),
    fix("Read the code: an LLM client wrapper", "hard", tag="GenAI",
        prompt="""This wrapper is used across a codebase. It is supposed to: pass a `timeout` to the transport, retry only
        `TimeoutError` and `ConnectionError` with exponential backoff (`base * 2 ** (attempt - 1)` seconds before retry `attempt`),
        raise `LLMCallError` from the last error when attempts run out, never include the API key in error messages, and let other
        exceptions propagate. Read it, find the bugs and fix them. (`sleep` and `transport` are injected.)""",
        code="""
        class LLMCallError(Exception):
            pass


        def complete(prompt, transport, api_key, sleep, attempts=3, base=0.5, timeout=20):
            for attempt in range(1, attempts + 1):
                try:
                    return transport(prompt, api_key=api_key)
                except Exception as e:
                    sleep(1)
                    error = e
            return ""
        """,
        tests="""
        def make(*outcomes):
            calls = []
            def transport(prompt, api_key, timeout=None):
                calls.append(timeout)
                out = outcomes[len(calls) - 1]
                if isinstance(out, Exception):
                    raise out
                return out
            return transport, calls

        waits = []
        t, calls = make(TimeoutError("t"), ConnectionError("c"), "answer")
        assert complete("hi", t, "sk-secret", waits.append) == "answer"
        assert calls == [20, 20, 20] and waits == [0.5, 1.0]

        waits = []
        t, calls = make(TimeoutError("a"), TimeoutError("b"), TimeoutError("c"))
        try:
            complete("hi", t, "sk-secret", waits.append, attempts=3)
            assert False
        except LLMCallError as e:
            assert isinstance(e.__cause__, TimeoutError) and "sk-secret" not in str(e) and waits == [0.5, 1.0]

        waits = []
        t, calls = make(ValueError("bad prompt for key sk-secret"), "never")
        try:
            complete("hi", t, "sk-secret", waits.append)
            assert False
        except ValueError:
            assert waits == [] and len(calls) == 1
        """,
        hints=["Three bugs: `except Exception` with a fixed `sleep(1)`, no `timeout=` passed, and `return \"\"` instead of raising.",
               "Do not sleep after the last attempt. Build the final message from the attempt count and the error type, not from `str(e)`, which could echo the key."],
        solution="""
        class LLMCallError(Exception):
            pass


        def complete(prompt, transport, api_key, sleep, attempts=3, base=0.5, timeout=20):
            last_error = None
            for attempt in range(1, attempts + 1):
                try:
                    return transport(prompt, api_key=api_key, timeout=timeout)
                except (TimeoutError, ConnectionError) as e:
                    last_error = e
                    if attempt < attempts:
                        sleep(base * 2 ** (attempt - 1))
            raise LLMCallError(f"LLM call failed after {attempts} attempts ({type(last_error).__name__})") from last_error
        """,
        why="""Five problems, each a real incident waiting to happen. **No timeout** reached the transport, so a hung connection would hang
        the caller for the SDK's default (minutes). **`except Exception`** retried a `ValueError` describing a bad prompt three times, and
        would retry bugs too. **A fixed `sleep(1)`** ignored the backoff policy, and also slept after the final attempt for nothing.
        **`return ""`** turned a total failure into an empty answer that the rest of the system would treat as the model's reply, the
        worst kind of swallowed error. And the final error message must not be built from `str(e)`, because exception messages from
        HTTP layers can include request details such as headers or URLs with keys; the fixed message names only the attempt count and
        error type, while the full original stays available as `__cause__` for internal logs, which should themselves be scrubbed. The
        `ValueError` now propagates after one call, untouched."""),
    write("A token bucket rate limiter", "hard", tag="GenAI",
        prompt="""To avoid 429s, throttle on the client side. Write `make_limiter(rate, burst, clock)` returning `acquire(cost=1)`.
        The bucket holds up to `burst` tokens, starts full, and refills continuously at `rate` tokens per second (using `clock()`).
        `acquire` takes `cost` tokens and returns `0.0` if they were available; otherwise it returns the number of seconds until
        enough tokens will exist, **without** taking any. Raise `ValueError` if `cost` exceeds `burst`.""",
        code="""
        def make_limiter(rate, burst, clock):
            pass
        """,
        tests="""
        now = [0.0]
        acquire = make_limiter(rate=2.0, burst=4, clock=lambda: now[0])
        assert [acquire() for _ in range(4)] == [0.0, 0.0, 0.0, 0.0]
        assert acquire() == 0.5
        now[0] = 0.5
        assert acquire() == 0.0 and acquire() == 0.5
        now[0] = 10.0
        assert acquire(4) == 0.0 and acquire(3) == 1.5
        now[0] = 11.5
        assert acquire(3) == 0.0
        try:
            acquire(5)
            assert False
        except ValueError:
            pass
        """,
        hints=["Keep `tokens` and `last` in the closure. On each call, add `(clock() - last) * rate` tokens, capped at `burst`, then update `last`.",
               "If `tokens >= cost`, subtract and return 0.0; otherwise return `(cost - tokens) / rate`."],
        solution="""
        def make_limiter(rate, burst, clock):
            tokens = float(burst)
            last = clock()

            def acquire(cost=1):
                nonlocal tokens, last
                if cost > burst:
                    raise ValueError(f"cost {cost} exceeds burst size {burst}")
                now = clock()
                tokens = min(burst, tokens + (now - last) * rate)
                last = now
                if tokens >= cost:
                    tokens -= cost
                    return 0.0
                return (cost - tokens) / rate

            return acquire
        """,
        why="""A token bucket allows short bursts (up to `burst` requests at once) while enforcing an average rate, which matches how
        providers express limits (requests or tokens per minute). Refilling lazily from the elapsed time, instead of with a timer,
        keeps it simple and exact. Returning the wait instead of sleeping keeps the limiter testable and lets the caller decide: sleep
        that long, or reject the request. Not taking tokens on a failed attempt is important; otherwise waiting callers would push
        each other further back. `cost` lets you meter tokens rather than requests: pass the estimated prompt tokens to respect a
        tokens-per-minute limit. In async code (14.5) the same bucket guards concurrent tasks with a lock."""),
    predict("Retry loops and exception links", "hard",
        code="""
        def attempt(n, fails):
            last = None
            for i in range(n):
                try:
                    if i < fails:
                        raise TimeoutError(f"t{i}")
                    return f"ok on {i}"
                except TimeoutError as e:
                    last = e
            else:
                raise RuntimeError("gave up") from last

        print(attempt(3, 1))
        try:
            attempt(2, 5)
        except RuntimeError as e:
            print(e, "|", e.__cause__, "|", e.__context__, "|", e.__cause__.__context__)

        def inside(n):
            for i in range(n):
                try:
                    raise TimeoutError(f"t{i}")
                except TimeoutError:
                    if i == n - 1:
                        raise RuntimeError("gave up inside")

        try:
            inside(2)
        except RuntimeError as e:
            print(e, "|", e.__cause__, "|", e.__context__)
        """,
        hints=["The `else` of a `for` loop runs when the loop ends without `break` or `return`.",
               "`__context__` is set only for exceptions raised while another is being handled."],
        why="""`attempt(3, 1)` fails once and returns on the second iteration. In `attempt(2, 5)`, both iterations fail, the loop finishes, and its
        `else` raises the `RuntimeError` **outside** any `except` block: so `__context__` is `None`, and the link exists only because of
        `from last`. Each `TimeoutError` was raised in a fresh iteration, after the previous handler had finished, so they are not
        chained to each other either. In `inside`, the `RuntimeError` is raised **inside** the handler, so Python links the last
        `TimeoutError` as context automatically, while `__cause__` stays `None`."""),
)

section("interview", "Interview questions",
    explain("Which errors from an LLM API should you retry, and how?", "medium", tag="Interview",
        why="""Retry transient failures: connection errors, timeouts, 429 rate limits, and server errors (500, 502, 503, 504 and
        overloaded responses such as 529). Do not retry 400-level errors other than 408, 409 and 429, because the same request will fail
        again: bad parameters, too many tokens (shorten the input instead), authentication and permission errors (alert instead).
        Retry with exponential backoff and jitter, honour `Retry-After` when the server sends it, cap the number of attempts, and wrap
        it all in an overall deadline so callers are not kept waiting longer than the feature can afford. Only retry operations that
        are safe to repeat, or use idempotency keys for ones that are not, because a timeout can happen after the server has done the
        work. Log each attempt with its error type and request id, and track retry and failure rates in metrics."""),
    explain("Why add jitter to retry delays?", "medium", tag="Interview",
        why="""Because failures are correlated. When a service hiccups, many clients fail at the same moment; with plain exponential
        backoff, they all wait exactly the same delays and retry in synchronised waves, each wave hitting the recovering service with
        the full load at once (the thundering herd problem). Jitter randomises each client's delay, typically choosing uniformly between
        zero and the exponential ceiling ("full jitter"), which spreads the retries evenly over time and lets the service recover. It also
        prevents accidental synchronisation of periodic jobs. AWS's architecture guidance on backoff and jitter showed that full jitter
        completes the work with far fewer total calls than backoff without jitter."""),
    explain("A nightly job sends 50,000 documents to an LLM for classification, and about 2% fail in different ways. How would you make it robust?", "hard", tag="Interview",
        why="""Classify the failures first, because each kind needs different handling. Transient errors (timeouts, rate limits, 5xx) get
        retries with backoff, ideally in rounds so stragglers do not block the batch, under a client-side rate limiter sized to the
        provider's limits, and with a circuit breaker so an outage pauses the job instead of burning through every document. Invalid
        output gets a repair attempt (send the error back to the model), then is recorded as failed. Truncated answers raise the token
        limit or shorten the input; context-length errors trim the document. Permanent failures (bad input) go to a dead-letter table with
        the document id, error type and request id. The job keeps every success, writes results idempotently keyed by document id with
        the model and prompt version, checkpoints progress so a crash resumes instead of restarting, and stops early if the failure rate
        exceeds an error budget, which signals a systemic issue. At the end it reports counts by outcome and error type, and a separate
        step reprocesses the dead-letter items after a fix. Finally, it samples outputs for quality evaluation, since a "successful"
        classification can still be wrong."""),
)

recap(
    "Sort failures by reaction: retry transient ones (timeouts, connection errors, 429, 5xx), fix bad requests, alert on auth errors, handle truncation and refusals explicitly.",
    "Retry with exponential backoff, jitter and `Retry-After`, a capped number of attempts and an overall deadline; inject `sleep`, `clock` and `rng` to test it.",
    "Retries are only safe for idempotent operations; use idempotency keys for the rest.",
    "Check `finish_reason`, validate output, and repair by sending the error back to the model a limited number of times.",
    "In batches, keep every success, isolate bad items, retry stragglers in rounds, and log type, status, request id and latency, never keys or raw personal data.",
)
