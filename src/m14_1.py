from lesson import *

lesson(
    id="m14-1", num="14.1", title="Concurrency concepts",
    intro="Before any API, the ideas that decide whether concurrency helps: CPU-bound versus I/O-bound work, concurrency versus "
          "parallelism, processes, threads and coroutines, the GIL and free-threaded Python, Amdahl's law and Little's law, and "
          "what goes wrong when tasks share state: races and deadlocks. Problems model these with small simulations, so the "
          "reasoning is exact and repeatable, which is also how you plan the concurrency of an LLM batch job.",
    desc="CPU-bound vs I/O-bound work, the GIL, free-threaded Python.",
    keys="concurrency parallelism cpu-bound io-bound process thread coroutine gil free-threaded pep 703 amdahl little's law throughput latency race condition lost update atomic lock deadlock lock ordering interleaving rate limit",
)

term("Concurrency", "Making progress on several tasks in overlapping time periods, for example by switching between them while each waits.")
term("Parallelism", "Executing several tasks at literally the same instant, on several CPU cores.")
term("GIL", "The Global Interpreter Lock of standard CPython: only one thread executes Python bytecode at a time in a process, so threads do not run Python code in parallel.")
term("Race condition", "A bug where the result depends on the timing or interleaving of concurrent tasks that share data.")

section("kinds", "Two kinds of slow",
    p("""A program is slow for one of two reasons, and the cure differs. **I/O-bound** work spends its time **waiting**: for a model API to answer, a database
    query, a file download, a disk read. The CPU is idle meanwhile, so the cure is to start other work during the wait; ten API calls that each take 2
    seconds can finish in about 2 seconds instead of 20. **CPU-bound** work spends its time **computing**: tokenising a corpus, computing features, parsing
    millions of JSON lines, resizing images. The only way to speed it up, apart from faster code, is to use more CPU cores at once."""),
    p("""Measure before choosing. Compare wall-clock time (`time.perf_counter()`) with CPU time (`time.process_time()`) for a task: if CPU time is close to wall
    time, it is CPU-bound; if it is a small fraction, the task mostly waits. Profilers (14.3, `cProfile`) show where the time goes. LLM applications are
    usually I/O-bound around the model call (network latency dominates) and CPU-bound in data preparation (chunking, embedding-free text processing,
    evaluation metrics over large sets)."""),
)

section("models", "Concurrency, parallelism and Python's three tools",
    p("""**Concurrency** means several tasks are in progress at once, with their execution interleaved; **parallelism** means several tasks execute at the same
    instant on different cores. One cook juggling three pots is concurrent; three cooks are parallel. Waiting work needs only concurrency; computing work
    needs parallelism."""),
    p("""Python offers three tools. **Processes** (`multiprocessing`, `ProcessPoolExecutor`, 14.3) each run their own interpreter with their own memory, so they
    compute in parallel on several cores; the costs are start-up time, memory, and the need to send data between them by serialising it. **Threads**
    (`threading`, `ThreadPoolExecutor`, 14.2) share one process's memory and are cheap to create; the operating system switches between them, so while one
    waits for the network, another runs. **Coroutines** (`asyncio`, 14.4 and 14.5) are functions that pause at `await` and let an event loop run others, all in
    one thread; they scale to thousands of concurrent waits with very little overhead, but only cooperate if every slow operation is awaited."""),
    p("""The rule of thumb: **I/O-bound with a moderate number of tasks: threads; I/O-bound with many tasks, or a codebase that is already async: asyncio;
    CPU-bound: processes** (or vectorised libraries such as NumPy, which release the GIL and use several cores internally)."""),
)

section("gil", "The GIL and free-threaded Python",
    p("""Standard CPython has a **Global Interpreter Lock**: a lock that a thread must hold to execute Python bytecode. It keeps the interpreter's internals (such
    as reference counts) consistent, but it means that in one process only **one thread runs Python code at a time**; the interpreter switches the lock between
    threads every few milliseconds (`sys.getswitchinterval()`, 5 ms by default). Two consequences follow. Threads give **no speed-up for pure-Python CPU work**,
    sometimes a slowdown from the switching. And threads **do** help for I/O, because a thread releases the GIL while it waits for the network or the disk,
    and C extensions such as NumPy, hashlib, zlib and many tokenizers release it during long computations."""),
    p("""The GIL does **not** make your code thread-safe. It protects the interpreter, not your data: a thread can be switched out between any two bytecode
    instructions, so a sequence such as reading a value, adding one, and writing it back can interleave with another thread doing the same (below). Shared
    mutable state still needs locks."""),
    p("""**Free-threaded Python** removes the GIL. PEP 703 added an optional build without it in Python 3.13 (installed as `python3.13t`), and Python 3.14 made that
    build officially supported (PEP 779), though not the default. In it, threads run Python code in parallel on several cores, at the cost of some
    single-thread overhead and of extensions that must be updated to declare they are safe. `sys._is_gil_enabled()` reports which mode is active. Python 3.14
    also added `concurrent.interpreters` and `InterpreterPoolExecutor` (PEP 734): several interpreters in one process, each with its own GIL, a middle ground
    between threads and processes. For the next few years, expect both builds in production, and code that is correct in either: protect shared state
    explicitly."""),
)

section("laws", "Two laws for planning",
    p("""**Amdahl's law** bounds the speed-up from parallelism. If a fraction `p` of the work can run in parallel and the rest is serial, `n` workers give a speed-up
    of `1 / ((1 - p) + p / n)`. With `p = 0.9`, eight workers give 4.7 times, and even infinitely many give only 10 times, because the serial 10% remains.
    Before parallelising a pipeline, find its serial parts: a single writer, a global lock, a step that must see all data."""),
    p("""**Little's law** connects concurrency, throughput and latency for any stable system: **the average number of tasks in progress equals the arrival rate
    times the average time each spends in the system**, `L = lambda * W`. For an LLM batch job it answers the planning question directly: to process 50
    requests per second when each call takes 2 seconds, you need about `50 * 2 = 100` calls in flight. Conversely, 10 concurrent workers with 2-second calls
    can never exceed 5 requests per second, however fast the rest of the code is. Rate limits (requests or tokens per minute) cap the same quantity from the
    other side, which is why concurrency must be limited, not maximised (14.5)."""),
)

section("races", "What goes wrong: races and deadlocks",
    p("""A **race condition** happens when tasks share mutable data and the result depends on how their steps interleave. The classic case is the **lost update**:
    two threads run `counter += 1`, which is really "read the value, add one, write it back"; if both read 5 before either writes, both write 6, and one
    increment is lost. The bug appears rarely, under load, and disappears when you add a print to debug it, which is what makes races expensive. The fix is to
    make the read-modify-write **atomic**: hold a `threading.Lock` around it, use a structure designed for concurrency (`queue.Queue`), or avoid shared
    mutable state altogether by giving each task its own data and combining results at the end (the approach executors encourage)."""),
    p("""A **deadlock** happens when tasks wait for each other forever: thread 1 holds lock A and waits for B while thread 2 holds B and waits for A. The standard
    prevention is a **global lock order**: every task acquires locks in the same order (for example sorted by id), so a cycle of waiting is impossible
    (problem 7). Timeouts on acquisition and holding locks for as little time as possible help too. In asyncio, the equivalent is awaiting something that can
    never happen; this site's event loop reports that instead of hanging."""),
    p("""Because real interleavings are invisible and non-deterministic, the problems below **simulate** them: each "thread" is a generator whose `yield` marks a
    point where the scheduler may switch, and a schedule lists which thread runs next. This is exactly how to reason about races on a whiteboard, and how tools
    that test concurrent code systematically (model checkers, deterministic schedulers) work."""),
    ex("""
    state = {"counter": 0}

    def increment():
        value = state["counter"]      # read
        yield                         # the scheduler may switch here
        state["counter"] = value + 1  # write

    def run(schedule):
        state["counter"] = 0
        threads = {"A": increment(), "B": increment()}
        for name in schedule:
            next(threads[name], None)
        return state["counter"]

    print(run(["A", "A", "B", "B"]), run(["A", "B", "A", "B"]), run(["B", "A", "A", "B"]))
    """, "lost_update.py"),
    p("""Run one after the other, the counter reaches 2. Interleaved so that both read before either writes, it ends at 1: an update was lost. Nothing about the
    code changed, only the timing."""),
)

section("site", "Concurrency on this site",
    p("""The browser cannot start threads or processes, and running asyncio needs a browser feature that is not yet universal. So on this site:
    `ThreadPoolExecutor`, `ProcessPoolExecutor` and `Thread.start` run each task **immediately, in order**, with the same API (results, exceptions, `map`,
    `submit`, `as_completed`), so your code is checked for correctness but not for speed; and `asyncio.run` uses an event loop with **simulated time**:
    `await asyncio.sleep(2)` returns at once but advances `asyncio.get_running_loop().time()` by exactly 2 seconds, so timings in the asyncio lessons are exact.
    Run the code locally to see real parallelism and real timings; the behaviour you are graded on is the same."""),
)

section("warmup", "Warm-up",
    predict("Timing models for three kinds of work", "easy",
        code="""
        durations = [2.0, 2.0, 2.0, 2.0]      # four tasks of 2 seconds each

        def sequential(tasks):
            return sum(tasks)

        def concurrent_io(tasks, workers):
            # waiting work overlaps: rounds of `workers` tasks
            rounds = -(-len(tasks) // workers)
            return rounds * max(tasks)

        def cpu_with_gil(tasks, threads):
            # only one thread computes at a time
            return sum(tasks)

        def cpu_with_processes(tasks, processes, startup=0.3):
            rounds = -(-len(tasks) // processes)
            return startup + rounds * max(tasks)

        print(sequential(durations), concurrent_io(durations, 4), concurrent_io(durations, 3))
        print(cpu_with_gil(durations, 4), cpu_with_processes(durations, 4), cpu_with_processes(durations, 2))
        print(-(-7 // 3), 7 // 3)
        """,
        hints=["`-(-a // b)` is ceiling division. With the GIL, threads take turns for Python computation."],
        why="""Four 2-second waits overlap completely with four workers, taking 2 seconds; with three workers, two rounds are needed. CPU work under the GIL gets no
        overlap, so four threads take as long as running sequentially, while four processes compute in parallel and pay a start-up cost. These idealised models
        are the first estimate to make before choosing a tool; real systems add overheads, but the shape holds."""),
    write("Amdahl's law", "easy", tag="ML",
        prompt="""Write `speedup(p, n)` returning Amdahl's speed-up for a parallel fraction `p` (between 0 and 1, else `ValueError`) and `n >= 1` workers, and
        `workers_for(p, target)` returning the smallest `n` reaching at least `target` (allowing for floating-point rounding), or `None` when the target is not
        below the limit `1 / (1 - p)`; for `p == 1` there is no limit and the answer is the smallest `n >= target`.""",
        code="""
        import math

        def speedup(p, n):
            pass

        def workers_for(p, target):
            pass
        """,
        tests="""
        assert round(speedup(0.9, 8), 2) == 4.71 and speedup(0.0, 64) == 1.0 and speedup(1.0, 8) == 8.0 and speedup(0.5, 1) == 1.0
        assert workers_for(0.9, 4) == 6 and workers_for(0.9, 4.0001) == 7 and workers_for(0.9, 10) is None and workers_for(0.9, 9.9) is not None and workers_for(1.0, 5) == 5
        assert workers_for(0.5, 1.0) == 1
        for bad in [(-0.1, 2), (1.1, 2), (0.5, 0)]:
            try:
                speedup(*bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["Solve `1 / ((1 - p) + p / n) >= target` for `n`: `n >= p / (1 / target - (1 - p))` when the denominator is positive.",
               "Use `math.ceil`, and guard floating-point edge cases by checking `speedup(p, n) >= target` (and incrementing if needed)."],
        solution="""
        import math


        def speedup(p, n):
            if not 0 <= p <= 1 or n < 1:
                raise ValueError("need 0 <= p <= 1 and n >= 1")
            return 1 / ((1 - p) + p / n)


        def workers_for(p, target):
            if target <= 1:
                return 1
            if p == 1:
                return math.ceil(target)
            room = 1 / target - (1 - p)
            if room <= 1e-12:
                return None
            n = max(1, math.floor(p / room))
            while speedup(p, n) < target - 1e-9:
                n += 1
            return n
        """,
        why="""Amdahl's formula says the serial part `1 - p` is paid in full however many workers you add, so the speed-up approaches `1 / (1 - p)`: 10 times for a 90%
        parallel job. Solving for `n` gives the workers needed, and the solution reports `None` when the target is beyond the limit, which is the useful answer in
        a planning discussion: "more machines will not get us there; we must shrink the serial part". The final loop compares with a tiny tolerance because 6 workers give
        exactly 4 times on paper but `3.9999999999999996` in floating point; without it, the answer would wrongly be 7. In data pipelines the serial part is often a single writer, a global aggregation, or loading a model once."""),
    fix("Little's law the wrong way round", "easy", tag="GenAI",
        prompt="""`concurrency_needed(target_rps, latency_s)` should return how many requests must be in flight to sustain `target_rps` requests per second when each takes
        `latency_s` seconds (rounded up), and `max_rps(concurrency, latency_s)` the best throughput a given concurrency allows. Both formulas are inverted. Fix them.""",
        code="""
        import math

        def concurrency_needed(target_rps, latency_s):
            return math.ceil(target_rps / latency_s)

        def max_rps(concurrency, latency_s):
            return concurrency * latency_s
        """,
        tests="""
        assert concurrency_needed(50, 2.0) == 100 and concurrency_needed(3, 0.5) == 2 and concurrency_needed(1, 0.25) == 1
        assert max_rps(10, 2.0) == 5.0 and max_rps(8, 0.5) == 16.0
        """,
        hints=["Little's law: items in flight = arrival rate x time in the system."],
        solution="""
        import math

        def concurrency_needed(target_rps, latency_s):
            return math.ceil(target_rps * latency_s)

        def max_rps(concurrency, latency_s):
            return concurrency / latency_s
        """,
        why="""Each in-flight request occupies a slot for `latency_s` seconds, so a slot serves `1 / latency_s` requests per second, and `concurrency` slots serve
        `concurrency / latency_s`; to reach a target rate you need `rate * latency` slots in flight. Units check the formulas: requests per second times seconds is
        a count of requests, and a count divided by seconds is a rate. This is why slow models need high concurrency for batch work, and why a provider's
        concurrency limit, not your code, often caps throughput."""),
    predict("Amdahl in numbers", "easy",
        code="""
        def speedup(p, n):
            return 1 / ((1 - p) + p / n)

        for p in (0.5, 0.9, 0.99):
            print(p, [round(speedup(p, n), 2) for n in (2, 8, 64, 1_000_000)])
        print(round(speedup(0.95, 16) / speedup(0.95, 8), 2))
        """,
        hints=["The limit is `1 / (1 - p)`: 2, 10 and 100."],
        why="""Speed-ups rise quickly at first and then flatten towards `1 / (1 - p)`: a half-serial job never gets past 2 times, a 90% parallel job past 10. Even at 99%,
        64 workers give under 40 times. Doubling from 8 to 16 workers on a 95% parallel job buys only about 50% more, which is why adding machines has diminishing
        returns and reducing the serial fraction is usually the bigger win."""),
)

section("medium", "Medium",
    write("Simulate a worker pool", "medium", tag="Data work",
        prompt="""Write `makespan(durations, workers)` simulating a pool of `workers` that takes tasks in order, each task going to the worker that becomes free first. Return
        `(total_time, finish_times)` where `finish_times[i]` is when task `i` completes. This is what a thread pool achieves for I/O-bound tasks.""",
        code="""
        import heapq

        def makespan(durations, workers):
            pass
        """,
        tests="""
        assert makespan([2, 2, 2, 2], 4) == (2, [2, 2, 2, 2])
        assert makespan([2, 2, 2, 2], 3) == (4, [2, 2, 2, 4])
        assert makespan([5, 1, 1, 1, 1, 1], 2) == (5, [5, 1, 2, 3, 4, 5])
        assert makespan([3, 1], 1) == (4, [3, 4]) and makespan([], 3) == (0, [])
        try:
            makespan([1], 0)
            assert False
        except ValueError:
            pass
        """,
        hints=["Keep a min-heap of the times at which each worker becomes free, starting with `[0] * workers`.",
               "For each task, pop the earliest free time, finish = that time + duration, push the finish time back."],
        solution="""
        import heapq


        def makespan(durations, workers):
            if workers < 1:
                raise ValueError("workers must be at least 1")
            free = [0] * workers
            finish = []
            for d in durations:
                start = heapq.heappop(free)
                end = start + d
                finish.append(end)
                heapq.heappush(free, end)
            return (max(finish) if finish else 0), finish
        """,
        why="""A heap of "free at" times always yields the worker available soonest, which is how an executor's queue behaves: the next task waits for the first free
        worker. The third case shows a key effect: one long task occupies a worker while the other handles the five short ones, so the total equals the long
        task's time. Ordering matters too: putting the longest tasks first (longest processing time first) usually reduces the makespan, which is why batch jobs
        with uneven tasks, such as documents of very different lengths, often sort by size before submitting."""),
    trace("Interleavings and the lost update", "medium",
        prompt="Fill in `result` after each marked line. Each thread reads the counter, yields (a possible switch), then writes the value it read plus one.",
        code="""
        state = {"counter": 0}

        def increment():
            value = state["counter"]
            yield
            state["counter"] = value + 1

        def run(schedule, n_threads=2):
            state["counter"] = 0
            threads = {name: increment() for name in "ABC"[:n_threads]}
            for name in schedule:
                next(threads[name], None)
            return state["counter"]

        result = run("AABB")  # row: "one after the other"
        result = run("ABAB")  # row: "both read first"
        result = run("ABBA")  # row: "nested"
        result = run("ABCABC", 3)  # row: "three readers"
        result = run("AABCBC", 3)  # row: "A finishes first"
        """,
        trace_vars=["result"],
        hints=["Each thread's first step reads, its second step writes. Track the value each thread read."],
        why="""When a thread completes its read and write before the other reads, its increment survives. Whenever both read the same value before either writes, the later
        write overwrites the earlier with the same number, and an increment is lost: `ABAB` and `ABBA` both end at 1. With three threads all reading 0 first, two
        increments are lost; if A finishes before B and C read, they both read 1 and the result is 2. The final value depends only on the interleaving, which is
        why race conditions are timing-dependent and hard to reproduce."""),
    fix("Locks taken in argument order", "medium", tag="Data work",
        prompt="""`transfer(src, dst, amount)` locks the source account, then the destination. If one thread runs `transfer(a, b, ...)` while another runs `transfer(b, a, ...)`,
        each can hold one lock and wait for the other forever. Fix it by always acquiring the two locks in a **global order** (by account name), and reject
        transfers from an account to itself with `ValueError` (taking the same non-reentrant lock twice would deadlock too). The `RecordingLock` stands in for
        `threading.Lock` and logs the order of acquisition.""",
        code="""
        class RecordingLock:
            log = []

            def __init__(self, name):
                self.name = name

            def __enter__(self):
                RecordingLock.log.append(self.name)
                return self

            def __exit__(self, *exc):
                return False


        class Account:
            def __init__(self, name, balance):
                self.name, self.balance = name, balance
                self.lock = RecordingLock(name)


        def transfer(src, dst, amount):
            with src.lock:
                with dst.lock:
                    if src.balance < amount:
                        raise ValueError("insufficient funds")
                    src.balance -= amount
                    dst.balance += amount
        """,
        tests="""
        RecordingLock.log.clear()
        a, b = Account("acct-a", 100), Account("acct-b", 50)
        transfer(a, b, 30)
        transfer(b, a, 10)
        assert RecordingLock.log == ["acct-a", "acct-b", "acct-a", "acct-b"]
        assert (a.balance, b.balance) == (80, 70)
        try:
            transfer(a, a, 5)
            assert False
        except ValueError:
            pass
        try:
            transfer(b, a, 1000)
            assert False
        except ValueError:
            pass
        assert (a.balance, b.balance) == (80, 70)
        """,
        hints=["`first, second = sorted((src, dst), key=lambda acct: acct.name)`, then `with first.lock, second.lock:`."],
        solution="""
        class RecordingLock:
            log = []

            def __init__(self, name):
                self.name = name

            def __enter__(self):
                RecordingLock.log.append(self.name)
                return self

            def __exit__(self, *exc):
                return False


        class Account:
            def __init__(self, name, balance):
                self.name, self.balance = name, balance
                self.lock = RecordingLock(name)


        def transfer(src, dst, amount):
            if src is dst:
                raise ValueError("cannot transfer to the same account")
            first, second = sorted((src, dst), key=lambda acct: acct.name)
            with first.lock, second.lock:
                if src.balance < amount:
                    raise ValueError("insufficient funds")
                src.balance -= amount
                dst.balance += amount
        """,
        why="""A deadlock needs a cycle of waiting, and a cycle needs two tasks acquiring the same locks in opposite orders. Sorting the accounts gives every transfer the same
        order, `acct-a` before `acct-b`, whichever direction the money flows, so no cycle can form; the recorded log shows exactly that. The balance check sits
        **inside** the locks, so no other transfer can change the balance between the check and the update (a "check-then-act" race). The same discipline applies
        to database row locks, file locks and asyncio locks: pick one order and use it everywhere."""),
    write("Throughput under a rate limit", "medium", tag="GenAI",
        prompt="""An LLM provider allows `rpm` requests per minute. Write `plan(n_requests, latency_s, rpm, max_concurrency)` returning a dict with `concurrency` (the
        concurrency that saturates the rate limit by Little's law, `ceil(rpm / 60 * latency_s)`, capped at `max_concurrency`), `rps` (the achievable requests per second,
        the smaller of `concurrency / latency_s` and `rpm / 60`), and `minutes` (the estimated time for the batch, `n_requests / rps / 60`, rounded to 1 decimal).""",
        code="""
        import math

        def plan(n_requests, latency_s, rpm, max_concurrency):
            pass
        """,
        tests="""
        p = plan(10_000, latency_s=3.0, rpm=600, max_concurrency=50)
        assert p == {"concurrency": 30, "rps": 10.0, "minutes": 16.7}
        q = plan(10_000, latency_s=3.0, rpm=600, max_concurrency=12)
        assert q == {"concurrency": 12, "rps": 4.0, "minutes": 41.7}
        assert plan(60, latency_s=0.5, rpm=6000, max_concurrency=100)["concurrency"] == 50
        assert plan(1, latency_s=0.1, rpm=60, max_concurrency=10)["concurrency"] == 1
        """,
        hints=["Rate in requests per second is `rpm / 60`; multiply by latency for the needed concurrency."],
        solution="""
        import math


        def plan(n_requests, latency_s, rpm, max_concurrency):
            rate_limit = rpm / 60
            concurrency = min(max(1, math.ceil(rate_limit * latency_s)), max_concurrency)
            rps = min(concurrency / latency_s, rate_limit)
            return {"concurrency": concurrency, "rps": rps, "minutes": round(n_requests / rps / 60, 1)}
        """,
        why="""Little's law turns a rate limit into a concurrency target: 10 requests per second with 3-second calls need 30 in flight. More concurrency would not help (the
        provider would answer with 429 errors), and less leaves throughput on the table: capped at 12, the batch takes 2.5 times longer. This back-of-the-envelope
        plan is what you do before writing the async batch runner of 14.5, and it tells you whether a 10,000-document job takes minutes or hours. Token-per-minute
        limits work the same way with tokens instead of requests."""),
    predict("Shared state and atomic steps", "medium",
        code="""
        state = {"counter": 0, "log": []}

        def unsafe(name):
            value = state["counter"]
            yield
            state["counter"] = value + 1
            state["log"].append(name)

        def safe(name):
            state["counter"] += 1        # read and write in one step: nothing can interleave
            state["log"].append(name)
            yield

        def run(make, schedule):
            state["counter"], state["log"] = 0, []
            threads = {n: make(n) for n in "AB"}
            for n in schedule:
                next(threads[n], None)
            return state["counter"], state["log"]

        print(run(unsafe, "ABAB"), run(safe, "ABAB"))
        print(run(unsafe, "BAAB"), run(safe, "BAAB"))
        """,
        hints=["In the simulation, a thread can only be switched out at `yield`. `safe` has no `yield` between reading and writing."],
        why="""In the unsafe version both threads read 0 before either writes, so the counter ends at 1 although both appended to the log, which is the signature of a lost
        update: two pieces of work done, one counted. The safe version performs the read-modify-write in one uninterrupted step, the simulation's equivalent of
        holding a lock, so every schedule gives 2. With real threads, `+=` is **not** one step (it is several bytecodes, and a switch can happen between them), which
        is why the real fix is a lock, not rewriting the line."""),
)

section("hard", "Hard",
    write("Enumerate every interleaving", "hard", tag="Data work",
        prompt="""Write `interleavings(counts)` yielding every schedule (a string) for threads named `A`, `B`, `C`, ... where thread `i` takes `counts[i]` steps, each schedule
        keeping each thread's own steps in order. Then write `outcomes(make_thread, counts, reset, read)`: for each schedule, call `reset()`, create one generator per
        thread with `make_thread(name)`, run the schedule, and collect `read()`; return the sorted list of distinct results. This is a tiny model checker.""",
        code="""
        def interleavings(counts):
            pass

        def outcomes(make_thread, counts, reset, read):
            pass
        """,
        tests="""
        assert sorted(interleavings([1, 1])) == ["AB", "BA"]
        assert len(list(interleavings([2, 2]))) == 6 and len(list(interleavings([2, 2, 2]))) == 90
        assert list(interleavings([2])) == ["AA"] and list(interleavings([])) == [""]

        state = {"x": 0}
        def reset():
            state["x"] = 0
        def read():
            return state["x"]

        def racy(name):
            v = state["x"]
            yield
            state["x"] = v + 1
            yield

        def atomic(name):
            state["x"] += 1
            yield
            yield

        assert outcomes(racy, [2, 2], reset, read) == [1, 2]
        assert outcomes(atomic, [2, 2], reset, read) == [2]
        assert outcomes(racy, [2, 2, 2], reset, read) == [1, 2, 3]
        """,
        hints=["Recursive generator: if every count is 0, yield `\"\"`; otherwise for each thread with steps left, yield its letter plus every interleaving of the counts with that one reduced.",
               "In `outcomes`, use a set of results and `next(gen, None)` for each scheduled step."],
        solution="""
        def interleavings(counts):
            counts = list(counts)
            if all(c == 0 for c in counts):
                yield ""
                return
            for i, c in enumerate(counts):
                if c:
                    counts[i] -= 1
                    for rest in interleavings(counts):
                        yield chr(ord("A") + i) + rest
                    counts[i] += 1


        def outcomes(make_thread, counts, reset, read):
            results = set()
            for schedule in interleavings(counts):
                reset()
                threads = {chr(ord("A") + i): make_thread(chr(ord("A") + i)) for i in range(len(counts))}
                for name in schedule:
                    next(threads[name], None)
                results.add(read())
            return sorted(results)
        """,
        why="""Testing concurrent code by running it many times only samples a few interleavings; **enumerating** them all proves what can happen. The number of schedules is the
        multinomial coefficient (6 for two threads of two steps, 90 for three), which grows fast, so real model checkers prune equivalent schedules, but the idea
        is this one. The racy increment can end anywhere from 1 to the number of threads, and the atomic one only at the correct total, which is a precise
        statement of why a critical section must not contain a switch point. The recursive generator mutates `counts` and restores it after each branch, a
        standard backtracking pattern (16.5)."""),
    write("Schedule requests under a sliding-window rate limit", "hard", tag="GenAI",
        prompt="""Write `schedule_requests(n, concurrency, latency, rpm=None)` returning the start time of each of `n` requests when at most `concurrency` run at once, each takes
        `latency` seconds, and (if `rpm` is given) at most `rpm` requests may **start** in any 60-second window. Requests start in order, each as soon as a worker is free
        and the rate limit allows (request `i` may not start before `starts[i - rpm] + 60`). Also write `finish_time(starts, latency)`.""",
        code="""
        import heapq

        def schedule_requests(n, concurrency, latency, rpm=None):
            pass

        def finish_time(starts, latency):
            pass
        """,
        tests="""
        assert schedule_requests(5, 2, 1.0) == [0.0, 0.0, 1.0, 1.0, 2.0]
        assert schedule_requests(5, 2, 1.0, rpm=3) == [0.0, 0.0, 1.0, 60.0, 60.0]
        starts = schedule_requests(100, 10, 2.0, rpm=60)
        assert starts[:12] == [0.0] * 10 + [2.0, 2.0] and starts[60] == 60.0 and finish_time(starts, 2.0) == 68.0
        assert schedule_requests(0, 3, 1.0) == [] and finish_time([], 1.0) == 0.0
        """,
        hints=["Keep a min-heap of worker free times starting at `[0.0] * concurrency`; for request `i`, the start is the popped time, then `max` it with the rate-limit bound.",
               "Push `start + latency` back for that worker."],
        solution="""
        import heapq


        def schedule_requests(n, concurrency, latency, rpm=None):
            free = [0.0] * concurrency
            starts = []
            for i in range(n):
                start = heapq.heappop(free)
                if rpm is not None and i >= rpm:
                    start = max(start, starts[i - rpm] + 60.0)
                starts.append(start)
                heapq.heappush(free, start + latency)
            return starts


        def finish_time(starts, latency):
            return max(starts) + latency if starts else 0.0
        """,
        why="""The simulation combines the two limits a real batch job faces: the pool's concurrency and the provider's rate limit. The rate limit says the `i`-th start must be
        at least a minute after the `(i - rpm)`-th, so once the first window's budget is used, the job waits for the window to slide, as the second case shows:
        the fourth request waits until second 60 although workers are free. With 60 requests per minute and 10 workers, the first 60 requests are done after 12
        seconds, then the job idles until the window slides at second 60 and finishes at 68 seconds instead of 22: it is rate-bound, and more workers would not help. Simulating before running a large batch avoids both 429 storms and pointless over-provisioning, and the
        same scheduler logic, with real sleeps, becomes the rate limiter of 14.5."""),
    write("Detect inconsistent lock orders", "hard", tag="Data work",
        prompt="""Write `lock_order_conflicts(tasks)` where `tasks` maps a task name to the list of lock names it acquires (holding each until the end, in that order). Return
        a sorted list of `(lock1, lock2, task1, task2)` tuples, with `lock1 < lock2` and `task1 < task2`, for every pair of locks that some task acquires as `lock1`
        before `lock2` and another acquires as `lock2` before `lock1`: each is a potential deadlock. Report each `(lock1, lock2, task1, task2)` once.""",
        code="""
        def lock_order_conflicts(tasks):
            pass
        """,
        tests="""
        tasks = {
            "transfer_ab": ["acct:a", "acct:b"],
            "transfer_ba": ["acct:b", "acct:a"],
            "report": ["acct:a", "acct:b", "acct:c"],
            "audit": ["acct:c", "acct:a"],
            "single": ["acct:b"],
        }
        assert lock_order_conflicts(tasks) == [
            ("acct:a", "acct:b", "report", "transfer_ba"),
            ("acct:a", "acct:b", "transfer_ab", "transfer_ba"),
            ("acct:a", "acct:c", "audit", "report"),
        ]
        assert lock_order_conflicts({"x": ["l1", "l2"], "y": ["l1", "l2"]}) == [] and lock_order_conflicts({}) == []
        """,
        hints=["For each task, record every ordered pair `(earlier, later)` of its locks, mapping the pair to the set of tasks that use that order.",
               "For each pair `(x, y)` with `x < y`, conflicts are tasks ordering `x` before `y` combined with tasks ordering `y` before `x`."],
        solution="""
        from itertools import combinations


        def lock_order_conflicts(tasks):
            orders = {}
            for task, locks in tasks.items():
                for earlier, later in combinations(locks, 2):
                    orders.setdefault((earlier, later), set()).add(task)
            conflicts = set()
            for (x, y), forward in orders.items():
                if x >= y:
                    continue
                for t1 in forward:
                    for t2 in orders.get((y, x), ()):
                        conflicts.add((x, y) + tuple(sorted((t1, t2))))
            return sorted(conflicts)
        """,
        why="""A deadlock between two tasks requires them to acquire two locks in opposite orders, so checking every ordered pair of acquisitions finds every potential
        two-task deadlock **statically**, without waiting for the unlucky timing. `combinations` yields each pair in acquisition order, so `report` contributes
        `a` before `b` and `a` before `c`, which conflicts with `audit` taking `c` first. This is the idea behind lock-order checkers such as the Linux kernel's
        lockdep and the "potential deadlock" warnings of thread sanitizers; the fix is always the same as in problem 7, one global order."""),
)

section("interview", "Interview questions",
    explain("What is the GIL, and when do threads help in Python?", "medium", tag="Interview",
        why="""The Global Interpreter Lock is a lock in standard CPython that a thread must hold to execute Python bytecode, so within one process only one thread runs Python
        code at a time; it simplifies memory management (reference counting) and C-extension safety. Threads therefore do not speed up pure-Python CPU-bound work.
        They do help for I/O-bound work, because a thread releases the GIL while waiting on sockets, files or sleeps, so other threads run meanwhile; and for code
        that spends its time in C extensions that release the GIL (NumPy, hashlib, compression, many tokenizers and image libraries). For CPU-bound Python code use
        processes, or vectorised libraries. The GIL does not make code thread-safe: compound operations can still interleave, so shared state needs locks. Python
        3.13 introduced an optional free-threaded build without the GIL (PEP 703), officially supported since 3.14, where threads can run Python in parallel, with
        some single-thread overhead and extension compatibility caveats."""),
    explain("Concurrency versus parallelism: explain the difference and how you would choose between threads, processes and asyncio.", "medium", tag="Interview",
        why="""Concurrency is structuring a program so several tasks make progress in overlapping time, by switching between them, typically while they wait; parallelism is
        executing several tasks at the same instant on multiple cores. Waiting (I/O-bound) work needs concurrency; computing (CPU-bound) work needs parallelism.
        In Python: **threads** for I/O-bound work with tens to hundreds of concurrent operations, especially when using blocking libraries; **asyncio** for large
        numbers of concurrent I/O operations (thousands of HTTP or LLM calls) with async-native libraries, at the cost of making the call chain async; **processes**
        for CPU-bound work such as parsing, feature extraction or batch inference on CPU, accepting start-up and serialisation costs. Measure first (wall versus CPU
        time), consider Amdahl's law for the achievable speed-up, and remember external limits such as rate limits, which often matter more than the tool."""),
    explain("You run 5,000 LLM calls for an evaluation and the provider allows 500 requests per minute. How do you plan the concurrency, and what can go wrong?", "hard", tag="Interview",
        why="""The rate limit caps throughput at 500/60, about 8.3 requests per second, so the job takes at least 10 minutes whatever the code does. By Little's law, with an average
        latency of, say, 3 seconds, about 25 requests in flight saturate the limit; more concurrency only produces 429 errors, less wastes time. I would use asyncio
        (or a thread pool) with a semaphore of about 25, plus a client-side rate limiter (token bucket or sliding window) so bursts stay under the limit, and respect
        token-per-minute limits too, by estimating tokens per request. Things that go wrong: 429s and timeouts, handled with retries, exponential backoff with jitter
        and honouring `Retry-After`; long-tail latency, handled with per-request timeouts; failures halfway, handled by writing results incrementally (JSONL) keyed
        by request id so the job can resume without repeating paid calls; non-determinism, handled by recording the model version and parameters; and cost, tracked
        from token usage as results arrive. Many providers also offer batch APIs at a discount with a delivery window, which is often the better choice for offline
        evaluation."""),
)

recap(
    "I/O-bound work waits and needs concurrency; CPU-bound work computes and needs parallelism; measure wall time against CPU time to tell them apart.",
    "Threads suit moderate I/O, asyncio suits many I/O operations, processes suit CPU work; the GIL stops threads from running Python code in parallel.",
    "Free-threaded Python (3.13 experimental, 3.14 supported) removes the GIL; the GIL never made shared state safe.",
    "Amdahl's law bounds speed-up by the serial fraction; Little's law (in flight = rate x latency) plans concurrency against rate limits.",
    "Races come from interleaved read-modify-write on shared state; deadlocks from inconsistent lock orders. Use locks, one global order, or no shared state.",
)
