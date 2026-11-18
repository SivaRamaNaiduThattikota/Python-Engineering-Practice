from lesson import *

lesson(
    id="m6-3", num="6.3", title="Generators and yield",
    intro="How a `for` loop really works (iterables, iterators, `next` and `StopIteration`), generator functions that "
          "pause at `yield`, generator expressions, `yield from`, cleanup with `finally`, and the traps: one-shot "
          "iteration, delayed errors and closed files. Applied to streaming files, JSONL, batches and LLM token streams.",
    desc="Iterators, `yield`, generator expressions, `yield from`, streaming data and LLM output.",
    keys="generator yield iterator iterable next stopiteration lazy generator expression yield from close finally exhaustion streaming jsonl batch llm stream sse memory",
)

term("Iterable", "Anything a `for` loop can walk over: lists, strings, dicts, files, ranges. Calling `iter()` on it returns an iterator.")
term("Iterator", "An object that produces values one at a time with `next()` and raises `StopIteration` when it has no more. It can be walked only once.")
term("Generator", "An iterator made by a function that contains `yield`. Each `next()` runs the function until the next `yield`, then pauses it, keeping its local variables.")
term("Lazy evaluation", "Computing values only when they are asked for, instead of all up front. Generators are lazy, lists are not.")

section("protocol", "How a `for` loop really works",
    p("""Every `for` loop in Python runs the same small protocol. An **iterable** is anything you can loop over: a list, a string, a
    dict, a file, a `range`. When the loop starts, Python calls `iter(iterable)`, which returns an **iterator**: an object that
    remembers where it is. Then, for every round, Python calls `next(iterator)` and binds the result to the loop variable. When
    the iterator has nothing left, `next` raises `StopIteration`, and the `for` loop catches it and ends quietly. You can run
    the protocol by hand:"""),
    ex("""
    words = ["refund", "policy"]
    it = iter(words)
    print(next(it), next(it))
    try:
        next(it)
    except StopIteration:
        print("StopIteration: the loop would end here")
    print(next(iter(words)), next(it, "default"))
    """, "protocol.py"),
    p("""`next(it, default)` returns the default instead of raising, which is the convenient form when "no more items" is a normal
    case. The important distinction is **iterable versus iterator**. A list is an iterable but not an iterator: each `iter(list)`
    gives a fresh iterator starting at the beginning, so you can loop over a list as many times as you like. An iterator is
    **one-shot**: it only moves forward, and once it is exhausted it stays empty. Calling `iter()` on an iterator returns the
    iterator itself, which is why looping over it a second time produces nothing."""),
    ex("""
    nums = [1, 2, 3]
    print(sum(nums), sum(nums))          # a list can be walked again
    it = iter(nums)
    print(sum(it), sum(it))              # an iterator only once
    print(iter(it) is it, iter(nums) is iter(nums))
    import io
    f = io.StringIO("line 1\\nline 2\\n")
    print([line.strip() for line in f], [line for line in f])   # files are iterators too
    """, "one_shot.py"),
    p("""Files are iterators over their lines, which is why reading a file twice in a row returns nothing the second time (you would
    need `f.seek(0)`). `zip`, `map`, `filter`, `enumerate`, `reversed`, dict views' iterators and everything in `itertools` (6.4)
    are iterators as well. This one-shot behaviour is the source of a whole family of bugs (problem 3)."""),
)

section("yield", "Generator functions: `yield` pauses a function",
    p("""A **generator function** is a normal `def` with at least one `yield` in its body. The `yield` changes what calling the
    function means. Calling it does **not** run the body; it immediately returns a **generator object**, which is an iterator.
    The body runs only when someone calls `next` on that object: it runs from the top **until the first `yield`**, hands that
    value to the caller, and **pauses**, keeping all of its local variables and its position. The next `next` resumes right
    after the `yield` and runs to the following one. When the body finishes (falls off the end or hits `return`), the generator
    raises `StopIteration`, and a `for` loop ends."""),
    ex("""
    def countdown(n):
        print(f"  start at {n}")
        while n > 0:
            yield n
            print(f"  resumed after yielding {n}")
            n -= 1
        print("  done")

    g = countdown(2)
    print("created", type(g).__name__)
    print("got", next(g))
    print("got", next(g))
    print("got", next(g, "nothing left"))
    """, "pause_resume.py"),
    p("""Follow the printed lines: "created" appears before "start", because creating the generator runs nothing. Each `next` runs
    the body only as far as the next `yield`. The local variable `n` survives between calls, which is what lets a generator
    produce a sequence without building it: it computes each value when asked, from the state it kept. That is called **lazy**
    evaluation. A generator that never finishes is fine, as long as the caller stops asking."""),
    ex("""
    def ids(prefix):
        n = 0
        while True:                      # infinite, and that is fine
            n += 1
            yield f"{prefix}-{n:04d}"

    gen = ids("TKT")
    print([next(gen) for _ in range(3)])
    for ticket in gen:
        if ticket.endswith("5"):
            break
    print(ticket, next(gen))
    """, "infinite.py"),
    p("""The `for` loop picked up where the comprehension left off, because both used the same generator: its state lives in the
    object, not in the loop. A `return value` inside a generator ends it; the value is attached to the `StopIteration`
    (`e.value`), which `yield from` uses (below) but a `for` loop ignores."""),
)

section("genexp", "Generator expressions",
    p("""A **generator expression** is the lazy version of a list comprehension: the same syntax with parentheses, `(expr for x in
    xs if cond)`. It returns a generator object at once, without computing anything; each value is computed when it is
    requested. When a generator expression is the only argument of a function, the extra parentheses can be dropped:
    `sum(x * x for x in xs)`."""),
    ex("""
    import sys

    squares_list = [x * x for x in range(1_000_000)]
    squares_gen = (x * x for x in range(1_000_000))
    print(f"list: {sys.getsizeof(squares_list) / 1_000_000:.1f} MB, generator: {sys.getsizeof(squares_gen)} bytes")
    print(sum(squares_gen), sum(squares_gen))      # the second sum finds it exhausted
    print(max(len(w) for w in "lazy evaluation saves memory".split()))
    """, "genexp_memory.py"),
    p("""The list holds a million references: about 4 MB for the list object alone on this page's 32-bit WebAssembly Python, and
    about 8 MB on a normal 64-bit machine, where each reference takes 8 bytes, not counting the integer objects themselves. The
    generator is a small fixed-size object whatever the length. That is why the generator form is the default for anything consumed
    **once**: `sum`, `min`, `max`, `any`, `all`, `sorted`, `"".join`, `dict(...)`, `set(...)`, or a `for` loop. It is also
    one-shot, as the second `sum` shows. Note that a generator is not automatically **faster**; for small data the list
    comprehension is often slightly quicker. The wins are memory, early exit (6.1) and being able to start working before all
    the data exists."""),
    p("""One detail of timing matters. In a generator expression, the **first** `for`'s iterable is evaluated immediately, when the
    expression is created; everything else (conditions, the expression, inner loops) is evaluated later, when values are
    requested. So rebinding the source name afterwards does not affect the generator, but changing a variable used in the
    expression does (problem 12)."""),
    ex("""
    xs = [1, 2, 3]
    g = (x * 10 for x in xs)
    xs = [7]                        # the generator already holds the old list
    print(list(g))
    factor = 2
    g = (x * factor for x in range(3))
    factor = 100                    # read later, when values are produced
    print(list(g))
    """, "genexp_binding.py"),
)

section("yieldfrom", "`yield from`, and cleanup with `finally`",
    p("""`yield from iterable` yields every value of another iterable, one by one, as if you had written `for v in iterable: yield v`.
    Its main use is **delegating** to another generator, especially in recursion: a function that walks a tree yields the
    current node and then `yield from` the walk of each child. When the inner iterable is a generator that `return`s a value,
    that value becomes the result of the `yield from` expression."""),
    ex("""
    def walk(node, depth=0):
        yield depth, node["title"]
        for child in node.get("children", []):
            yield from walk(child, depth + 1)

    doc = {"title": "Policy", "children": [
        {"title": "Refunds", "children": [{"title": "EU"}, {"title": "US"}]},
        {"title": "Contact"}]}
    print(["  " * d + t for d, t in walk(doc)])

    def inner():
        yield "a"
        return "inner finished"

    def outer():
        result = yield from inner()
        yield result
    print(list(outer()))
    """, "yield_from.py"),
    p("""A generator can hold resources, such as an open file or a network connection, while it is paused. If the caller stops early
    (a `break`, an exception, or simply dropping the generator), the generator is **closed**: Python raises `GeneratorExit`
    inside it at the paused `yield`, so its `finally` blocks and `with` blocks run and release the resource. `g.close()` does
    this explicitly; otherwise it happens when the generator is garbage-collected, which in CPython is usually immediately after
    the last reference goes away."""),
    ex("""
    def stream_lines(lines):
        print("  open")
        try:
            for line in lines:
                yield line
        finally:
            print("  closed")

    for line in stream_lines(["a", "b", "c"]):
        print(line)
        if line == "b":
            break
    print("after the loop")
    """, "cleanup.py"),
    p("""Generators can also receive values with `g.send(value)`, which makes `yield` an expression that returns what was sent. That
    is how coroutines worked before `async` and `await`; you will meet the modern form in the async module, and you rarely need
    `send` in everyday code."""),
)

section("traps", "The traps: one-shot, delayed errors and closed files",
    p("""Generators remove a lot of memory pressure, but they move **when** code runs, which creates three classic bugs."""),
    p("""**One-shot consumption.** A function that receives an iterable and loops over it twice (say, once for the mean and once for
    the maximum) works with a list and silently breaks with a generator: the second pass sees nothing. Either take one pass that
    computes everything, or turn the input into a list once at the start, `items = list(items)`, when you know it fits in memory
    (problem 3)."""),
    p("""**Delayed errors.** The body of a generator function, including argument checks at the top, runs only on the first `next`.
    So `batched(items, 0)` does not raise where it is called; it raises later, wherever the generator is first consumed, which can
    be far away and confusing. The fix is to split the function: a normal function validates the arguments and then returns the
    inner generator (problem 6)."""),
    ex("""
    def lazy_check(n):
        if n < 1:
            raise ValueError("n must be at least 1")
        yield from range(n)

    g = lazy_check(0)
    print("no error yet:", type(g).__name__)
    try:
        next(g)
    except ValueError as e:
        print("raised only now:", e)

    def eager_check(n):
        if n < 1:
            raise ValueError("n must be at least 1")
        return (i for i in range(n))     # a normal function returning a generator
    try:
        eager_check(0)
    except ValueError as e:
        print("raised at the call:", e)
    """, "delayed_errors.py"),
    p("""**Closed resources.** `with open(path) as f: return (json.loads(l) for l in f)` returns a generator, and then the `with`
    block ends and **closes the file** before anyone has read a line; iterating raises `ValueError: I/O operation on closed
    file`. Put the `with` **inside a generator function** and `yield` from within it, so the file stays open exactly as long as
    the generator is being consumed, and closes when it finishes or is closed (problem 14)."""),
    p("""Two smaller points. A generator has no `len()` and cannot be indexed, because its values do not exist yet; use
    `sum(1 for _ in g)` to count (which consumes it) or keep a counter. And for debugging, `list(g)` shows what a generator
    produces, at the price of consuming it."""),
)

section("streaming", "Generators in data and GenAI code",
    p("""The common thread of everything above is **streaming**: process data as it arrives, one piece at a time, with memory that
    does not grow with the input. Three patterns cover most real uses. **Reading large files:** a generator that opens the file,
    yields one parsed record per line, and skips or reports bad lines, so a 50 GB JSON Lines file needs only one line of memory at
    a time (problem 2). **Pipelines:** each step is a generator that takes an iterable and yields transformed items, so chaining
    steps builds a lazy pipeline that does no work until the end is consumed (6.4). **Streaming model output:** LLM APIs can send
    a reply as a stream of small text pieces, and a generator is the natural way to represent it."""),
    ex("""
    import time

    def fake_llm_stream(reply, delay=0.0):
        # stands in for an SDK's streaming iterator: one small piece at a time
        for piece in reply.split(" "):
            time.sleep(delay)
            yield piece + " "

    def with_progress(stream):
        text = ""
        for delta in stream:
            text += delta
            yield text.rstrip()        # what a UI would show after each piece

    for shown in with_progress(fake_llm_stream("Refunds take five days.")):
        print(repr(shown))
    """, "llm_stream.py"),
    p("""Real SDKs work the same way: with `stream=True`, the client returns an iterator of events, and your code loops over it,
    printing or forwarding each delta as it arrives, so the user sees the first words within a fraction of a second instead of
    waiting for the whole reply. Web frameworks accept generators directly for this: FastAPI's `StreamingResponse` takes a
    generator and sends each yielded chunk to the browser as soon as it is produced. And if the user closes the page, the
    framework closes the generator, so its `finally` block is the place to stop the upstream request and log usage. In ML
    training code, PyTorch's `IterableDataset` is a class whose `__iter__` is a generator that yields training examples, which is
    how datasets larger than memory are fed to a model."""),
)

section("warmup", "Warm-up",
    predict("Iterators are one-shot", "easy",
        code="""
        nums = [3, 1, 2]
        it = iter(nums)
        print(next(it), list(it), list(it))
        g = (n * 2 for n in nums)
        print(sum(g), sum(g), max(nums), sorted(nums) == sorted(nums))
        z = zip("ab", [1, 2])
        print(list(z), dict(z))
        """,
        hints=["A list can be walked many times; an iterator, a generator expression and a `zip` object only once."],
        why="""After one `next`, `list(it)` takes the remaining two items and leaves the iterator exhausted, so the second `list` is
        empty. The generator expression is used up by the first `sum`, so the second `sum` adds nothing and returns 0. The list
        `nums` itself can be walked again and again. `zip` is an iterator too: `list(z)` consumes it, and `dict(z)` then builds an
        empty dict, a classic bug when a zip object is stored in a variable and used twice."""),
    write("Read JSON Lines lazily", "easy", tag="Data work",
        prompt="""Write a generator function `read_jsonl(lines)` that takes any iterable of text lines (a list, a file) and yields
        one parsed object per line, skipping lines that are empty or only whitespace. It must not build a list.""",
        code="""
        import json

        def read_jsonl(lines):
            pass
        """,
        tests="""
        import inspect
        lines = ['{"id": 1, "text": "Refund"}\\n', "\\n", '  {"id": 2, "text": "Reset"}  \\n', "   \\n"]
        assert inspect.isgeneratorfunction(read_jsonl)
        assert list(read_jsonl(lines)) == [{"id": 1, "text": "Refund"}, {"id": 2, "text": "Reset"}]
        assert list(read_jsonl([])) == []
        g = read_jsonl(iter(['{"a": 1}', "not json"]))
        assert next(g) == {"a": 1}
        """,
        hints=["Loop over `lines`, `continue` on blank ones, and `yield json.loads(line)` for the rest."],
        solution="""
        import json

        def read_jsonl(lines):
            for line in lines:
                if line.strip():
                    yield json.loads(line)
        """,
        why="""Because of `yield`, calling `read_jsonl` returns a generator and parses nothing until asked. The last test shows the
        laziness: the second line is not valid JSON, but `next(g)` only parses the first one, so no error happens yet.
        `json.loads` ignores surrounding whitespace, so the stripped check is only needed to skip blank lines. Passing an open
        file as `lines` streams a file of any size with one line in memory at a time."""),
    fix("Statistics that break on a generator", "easy", tag="ML",
        prompt="""`summary(scores)` returns `(mean, maximum)`. It works on lists but fails with a `ValueError` when given a
        generator of scores. Fix it so it works with any iterable, in a single pass over the data.""",
        code="""
        def summary(scores):
            total = 0
            count = 0
            for s in scores:
                total += s
                count += 1
            return total / count, max(scores)
        """,
        tests="""
        assert summary([2, 9, 4]) == (5.0, 9)
        assert summary(s for s in [2, 9, 4]) == (5.0, 9)
        assert summary(iter([2])) == (2.0, 2)
        """,
        hints=["The `for` loop exhausts the generator, so `max(scores)` sees an empty iterator. Track the maximum inside the same loop."],
        solution="""
        def summary(scores):
            total, count, best = 0, 0, None
            for s in scores:
                total += s
                count += 1
                if best is None or s > best:
                    best = s
            return total / count, best
        """,
        why="""The loop consumed every value, so `max` received an exhausted iterator and raised `ValueError: max() iterable argument is
        empty`. With a list, a second pass works, which is why the bug hides in tests that use lists. Computing everything in one
        pass works for any iterable, including a file or a stream too large to keep. The alternative, `scores = list(scores)` at
        the top, is fine when the data fits in memory, and is the usual choice when you need several passes."""),
    predict("When the body runs", "easy",
        code="""
        def gen():
            print("A")
            yield 1
            print("B")
            yield 2
            print("C")

        g = gen()
        print("created")
        for value in g:
            print("got", value)
        print(list(gen())[-1])
        """,
        hints=["Creating a generator runs nothing. Each `next` (each round of the `for`) runs the body up to the next `yield`."],
        why="""`gen()` returns at once, so "created" comes first. The loop's first `next` prints A and yields 1; the second resumes, prints
        B and yields 2; the third prints C, falls off the end and raises `StopIteration`, ending the loop. `list(gen())` runs a new
        generator to completion, so A, B and C print again before the list is complete and its last item, 2, is printed."""),
)

section("medium", "Medium",
    write("Show a streamed reply as it grows", "medium", tag="GenAI",
        prompt="""A chat UI re-renders the reply after each streamed piece. Write a generator `accumulate(deltas)` that takes an
        iterable of text pieces and yields the full text so far after each **non-empty** piece. After the stream ends, the
        generator should `return` the final text, so a caller using `yield from` can get it.""",
        code="""
        def accumulate(deltas):
            pass
        """,
        tests="""
        assert list(accumulate(["Re", "", "funds ", "take", " 5 days."])) == ["Re", "Refunds ", "Refunds take", "Refunds take 5 days."]
        assert list(accumulate([])) == []

        def ui(deltas):
            final = yield from accumulate(deltas)
            yield f"FINAL: {final}"
        assert list(ui(["a", "b"])) == ["a", "ab", "FINAL: ab"]
        assert list(ui([""])) == ["FINAL: "]
        """,
        hints=["Keep the pieces in a list and yield `\"\".join(parts)` after each non-empty one, or build the string with `+=` (fine for short replies).",
               "`return text` at the end of a generator becomes the value of `yield from`."],
        solution="""
        def accumulate(deltas):
            text = ""
            for delta in deltas:
                if delta:
                    text += delta
                    yield text
            return text
        """,
        why="""Each yielded value is the whole text so far, which is what a UI needs to redraw; skipping empty deltas avoids pointless
        redraws (streams often send empty pieces at the start or around tool calls). The `return text` ends the generator and puts
        the text on the `StopIteration`, which `yield from` turns into its result, so the wrapper gets the final reply without
        rebuilding it. `+=` on a string is fine for a chat reply; for very long streams, collect pieces in a list and join (5.1)."""),
    fix("A batch generator that fails late", "medium", tag="Data work",
        prompt="""`batched(items, n)` yields lists of `n` items. Called with `n=0`, it should raise `ValueError` **immediately**,
        at the call, not later when the batches are consumed in a different part of the program. Fix it.""",
        code="""
        def batched(items, n):
            if n < 1:
                raise ValueError("n must be at least 1")
            batch = []
            for item in items:
                batch.append(item)
                if len(batch) == n:
                    yield batch
                    batch = []
            if batch:
                yield batch
        """,
        tests="""
        assert list(batched(range(5), 2)) == [[0, 1], [2, 3], [4]]
        try:
            batched([1, 2], 0)
            assert False, "should raise at the call"
        except ValueError:
            pass
        assert list(batched([], 3)) == []
        """,
        hints=["A generator function's body, including the check, only runs on the first `next`. Validate in a normal function, then return an inner generator."],
        solution="""
        def batched(items, n):
            if n < 1:
                raise ValueError("n must be at least 1")
            return _batches(items, n)


        def _batches(items, n):
            batch = []
            for item in items:
                batch.append(item)
                if len(batch) == n:
                    yield batch
                    batch = []
            if batch:
                yield batch
        """,
        why="""Because the original body contains `yield`, the whole function is a generator function: calling it only creates the
        generator, and the `if n < 1` line runs on the first `next`, possibly much later, in code that has nothing to do with the
        mistake. Splitting it in two makes `batched` an ordinary function that validates eagerly and returns the generator from
        `_batches`. The callers see no other difference. Libraries use this pattern whenever arguments of a lazy function need
        checking."""),
    write("Batches from any iterable, lazily", "medium", tag="GenAI",
        prompt="""Write a generator `chunks_of(iterable, n)` yielding tuples of up to `n` items. It must work with **any**
        iterable, including generators and infinite ones, and must not read more items than it needs: taking the first batch of
        an infinite generator must work. (`n` is at least 1; you do not need to validate it.)""",
        code="""
        def chunks_of(iterable, n):
            pass
        """,
        tests="""
        assert list(chunks_of("abcde", 2)) == [("a", "b"), ("c", "d"), ("e",)]
        assert list(chunks_of([], 3)) == []

        def naturals():
            i = 0
            while True:
                i += 1
                yield i
        g = chunks_of(naturals(), 3)
        assert next(g) == (1, 2, 3) and next(g) == (4, 5, 6)

        pulled = []
        def tracked():
            for i in range(10):
                pulled.append(i)
                yield i
        first = next(chunks_of(tracked(), 4))
        assert first == (0, 1, 2, 3) and pulled == [0, 1, 2, 3]
        """,
        hints=["You cannot slice a generator. Get one iterator with `it = iter(iterable)`, and fill each batch with `next(it, sentinel)` until it is full or the sentinel appears.",
               "A unique `sentinel = object()` tells \"no more items\" apart from items like `None`."],
        solution="""
        def chunks_of(iterable, n):
            it = iter(iterable)
            done = object()
            while True:
                batch = []
                for _ in range(n):
                    item = next(it, done)
                    if item is done:
                        break
                    batch.append(item)
                if batch:
                    yield tuple(batch)
                if len(batch) < n:
                    return
        """,
        why="""Slicing (`items[i:i + n]`) only works on sequences, so a general version must pull items with `next`. Calling `iter` once is
        essential: the same iterator is shared by all batches, so each batch continues where the last stopped. A private sentinel
        object is the safe "no more" marker, since any real value, including `None`, could appear in the data. Pulling exactly `n`
        items per batch and stopping as soon as one batch is short means an infinite source is fine and no item is read early,
        which the `pulled` test checks. This is what `itertools.batched` (Python 3.12+) does, built on `islice` (6.4); sending
        embeddings in batches from a stream is the typical use."""),
    choose("The first five matches: build everything or stop early", "medium",
        prompt="Both collect the first 5 ticket ids divisible by 7 from 1,000,000 ids. Which is faster?",
        setup="""ids = list(range(1, 1_000_001))""",
        options={
            "a": "first = [i for i in ids if i % 7 == 0][:5]",
            "b": "first = []\nfor i in (i for i in ids if i % 7 == 0):\n    first.append(i)\n    if len(first) == 5:\n        break",
        },
        answer="b",
        hints=["How many ids does each version check?"],
        why="""The list comprehension checks all million ids and builds a list of about 143,000 matches, then keeps five. The generator
        version checks ids only until the fifth match (35 ids) and stops, because the `break` stops asking the generator for more.
        The generator is not faster per item; it wins by not doing the work at all. `itertools.islice(gen, 5)` (6.4) is the
        one-line form of this pattern."""),
    trace("A generator step by step", "medium",
        prompt="Fill in `r` and `calls` after each marked line.",
        code="""
        calls = 0

        def numbers():
            global calls
            for n in [10, 20, 30]:
                calls += 1
                yield n

        g = numbers()
        r = "created"  # row: "after creating g"
        r = next(g)  # row: "first next"
        r = next(g) + next(g)  # row: "two more"
        r = next(g, "empty")  # row: "exhausted"
        r = sum(numbers())  # row: "a new generator"
        """,
        trace_vars=["r", "calls"],
        hints=["Creating `g` runs nothing, so `calls` stays 0. Each `next` runs the loop once more."],
        why="""`calls` counts how far the body has run. It is 0 after creating the generator, because the body has not started. Each
        `next` advances one round of the loop. After three values, the fourth `next` finds the loop finished and returns the
        default instead of raising. `sum(numbers())` uses a **new** generator object, which runs from the start, adding three more
        calls."""),
    write("A streaming SSE parser as a generator", "medium", tag="GenAI",
        prompt="""Turn the streaming reader from 5.P into a generator. `deltas(chunks)` takes an iterable of `bytes` chunks of
        server-sent events (lines like `data: {"delta": "Hi"}`, possibly ending in `\\r\\n`, split anywhere, even inside a
        character) and **yields** each delta as soon as its line is complete. It stops at `data: [DONE]` and ignores other lines.""",
        code="""
        import json

        def deltas(chunks):
            pass
        """,
        tests="""
        body = 'data: {"delta": "Caf\\u00e9 "}\\r\\n: keep-alive\\r\\ndata: {"delta": "ok"}\\r\\ndata: [DONE]\\r\\ndata: {"delta": "x"}\\r\\n'
        raw = body.encode("utf-8")
        assert list(deltas(raw[i:i + 3] for i in range(0, len(raw), 3))) == ["Café ", "ok"]

        sent = []
        def network():
            for i in range(0, len(raw), 7):
                sent.append(i)
                yield raw[i:i + 7]
        g = deltas(network())
        assert next(g) == "Café "
        assert len(sent) < 6
        """,
        hints=["Same buffer logic as 5.P: append each chunk to a `bytes` buffer, split off complete lines at `b\"\\n\"`, decode each line, strip `\\r`.",
               "`yield` each delta instead of appending it to a list, and `return` at `[DONE]`."],
        solution="""
        import json

        def deltas(chunks):
            buffer = b""
            for chunk in chunks:
                buffer += chunk
                while b"\\n" in buffer:
                    raw_line, buffer = buffer.split(b"\\n", 1)
                    line = raw_line.decode("utf-8").rstrip("\\r")
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload == "[DONE]":
                        return
                    yield json.loads(payload)["delta"]
        """,
        why="""The parsing logic is the same as in 5.P; the change is that results are **yielded** as soon as each line is complete,
        instead of collected and returned at the end. The second test checks the point of the change: the first delta is available
        after only a few network chunks, so a UI can show the first words while the rest is still arriving. `return` at `[DONE]`
        ends the generator, and since the caller drives the loop, it can also stop early with `break`, which closes the generator.
        Lines starting with `:` are SSE comments, commonly used as keep-alives, and are skipped like any other non-data line."""),
    refactor("A list builder to a streaming generator", "medium", tag="Data work",
        prompt="Rewrite `clean_rows` as a generator function that yields each cleaned row. The tests use `list(...)`, so they stay green.",
        code="""
        def clean_rows(rows):
            out = []
            for row in rows:
                if not row.strip() or row.startswith("#"):
                    continue
                parts = [p.strip() for p in row.split(",")]
                if len(parts) != 3:
                    continue
                out.append({"id": int(parts[0]), "name": parts[1], "score": float(parts[2])})
            return out
        """,
        tests="""
        rows = ["# id,name,score", "1, Ana , 0.9", "", "2,Bo", "3,Cy,0.75"]
        assert list(clean_rows(rows)) == [{"id": 1, "name": "Ana", "score": 0.9}, {"id": 3, "name": "Cy", "score": 0.75}]
        assert list(clean_rows([])) == []
        """,
        hints=["Replace `out.append(...)` with `yield ...`, and remove the list and the `return`."],
        solution="""
        def clean_rows(rows):
            for row in rows:
                if not row.strip() or row.startswith("#"):
                    continue
                parts = [p.strip() for p in row.split(",")]
                if len(parts) != 3:
                    continue
                yield {"id": int(parts[0]), "name": parts[1], "score": float(parts[2])}
        """,
        why="""The change is mechanical: every `out.append(x)` becomes `yield x`, and the result list disappears. The behaviour changes in
        the useful way: memory no longer grows with the input, the first row is available immediately, and the function works on an
        open file or another generator of any size. Callers that need a list write `list(clean_rows(rows))`. The trade-off is
        one-shot iteration: a caller that loops twice must store the result first."""),
    predict("What a generator expression captures", "medium",
        code="""
        data = [1, 2, 3]
        g1 = (x * 10 for x in data)
        data = [7, 8]
        print(list(g1))
        data2 = [1, 2, 3]
        g2 = (x * 10 for x in data2)
        data2.append(4)
        print(list(g2))
        k = 1
        g3 = (x + k for x in range(3))
        k = 50
        print(list(g3), list(g3))
        """,
        hints=["The first iterable is evaluated when the generator is created; everything else when values are produced.",
               "Rebinding a name is not the same as changing the object it refers to."],
        why="""`g1` grabbed the **list object** `[1, 2, 3]` when it was created; rebinding `data` to a new list does not affect it.
        `g2` also holds its list, but `append` **changes** that same object before the generator runs, so the 4 is included, the
        alias effect of 2.2. `k` in the expression is looked up only when each value is produced, after `k = 50`. The second
        `list(g3)` is empty because the generator is exhausted."""),
)

section("hard", "Hard",
    write("Walk a document outline", "hard", tag="RAG",
        prompt="""Chunkers for structured documents keep each section's heading path, such as `Policy > Refunds > EU`, as metadata.
        Write a generator `section_paths(node, sep=" > ")` that walks a tree of `{"title": ..., "children": [...]}` nodes
        (`children` may be missing) and yields the path of every node, parents before children, using `yield from` for the
        recursion.""",
        code="""
        def section_paths(node, sep=" > "):
            pass
        """,
        tests="""
        doc = {"title": "Policy", "children": [
            {"title": "Refunds", "children": [{"title": "EU"}, {"title": "US", "children": []}]},
            {"title": "Contact"}]}
        assert list(section_paths(doc)) == ["Policy", "Policy > Refunds", "Policy > Refunds > EU", "Policy > Refunds > US", "Policy > Contact"]
        assert list(section_paths({"title": "Solo"})) == ["Solo"]
        assert next(section_paths(doc, sep="/")) == "Policy"
        deep = {"title": "0"}
        node = deep
        for i in range(1, 50):
            node["children"] = [{"title": str(i)}]
            node = node["children"][0]
        assert list(section_paths(deep))[-1].count(" > ") == 49
        """,
        hints=["Use a helper with a `prefix` parameter: yield `prefix + title`, then `yield from` the helper on each child with the new path as prefix."],
        solution="""
        def section_paths(node, sep=" > "):
            yield from _paths(node, sep, "")


        def _paths(node, sep, prefix):
            path = f"{prefix}{sep}{node['title']}" if prefix else node["title"]
            yield path
            for child in node.get("children", []):
                yield from _paths(child, sep, path)
        """,
        why="""Each call yields its own path and then delegates to the calls for its children with `yield from`, which passes their values
        straight through to the caller. Passing the path down as a parameter means no node needs to know about its parents. The
        walk is lazy: `next(...)` gets the first path without visiting the rest of the tree. Depth is limited by the recursion
        limit (about 1,000 by default), which is plenty for document outlines; for unbounded depth, an explicit stack in a loop
        avoids recursion. LlamaIndex and LangChain's Markdown header splitters attach exactly this kind of heading path to each
        chunk so retrieval results can show where they came from."""),
    fix("Read the code: a loader that reads a closed file", "hard", tag="Data work",
        prompt="""This loads training records from a JSON Lines file and takes the first `n`. It crashes with `ValueError: I/O
        operation on closed file`. Once that is fixed, it returns one record too many, and a single bad line stops the whole run,
        when bad lines should be skipped and their line numbers recorded in `errors`. Read it, find the bugs and fix them.""",
        code="""
        import json


        def load_records(path, errors):
            with open(path, encoding="utf-8") as f:
                return (json.loads(line) for line in f if line.strip())


        def first_n(records, n):
            out = []
            for i, record in enumerate(records):
                if i > n:
                    break
                out.append(record)
            return out
        """,
        tests="""
        import os, tempfile
        p = os.path.join(tempfile.mkdtemp(), "train.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"text": "a", "label": 1}\\n\\n{broken\\n{"text": "b", "label": 0}\\n{"text": "c", "label": 1}\\n')
        errors = []
        assert first_n(load_records(p, errors), 2) == [{"text": "a", "label": 1}, {"text": "b", "label": 0}]
        assert errors == [3]
        errors = []
        assert len(first_n(load_records(p, errors), 10)) == 3 and errors == [3]
        assert first_n(load_records(p, []), 0) == []
        """,
        hints=["`return (generator)` inside `with` returns, and the `with` closes the file before the generator runs. Make `load_records` itself a generator: `yield` inside the `with`.",
               "Use `enumerate(f, start=1)` for line numbers and `try` / `except json.JSONDecodeError` around `json.loads`.",
               "`if i > n` lets index `n` through, which is item `n + 1`. Stop when `i == n` (before appending)."],
        solution="""
        import json


        def load_records(path, errors):
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        errors.append(lineno)


        def first_n(records, n):
            out = []
            for i, record in enumerate(records):
                if i == n:
                    break
                out.append(record)
            return out
        """,
        why="""Bug one is the classic generator-and-resource trap: the generator expression is created, `return` leaves the `with` block,
        and the file closes before a single line is read. With `yield` **inside** the `with`, the function itself is the generator,
        so the file stays open while records are being pulled and closes when the generator finishes or is closed (when `first_n`
        breaks out early and drops it). Bug two is an off-by-one: `i > n` allows indices `0..n`, which is `n + 1` records. Bug
        three: one corrupt line raised `JSONDecodeError` and killed the run; catching it per line, recording the line number and
        continuing is the standard behaviour for large training files, where a few bad lines are normal. Note that the error for
        line 3 is only recorded because the loader reached line 3; with a lazy loader, errors after the last record you consume are
        never seen."""),
    write("A shuffle buffer for streams", "hard", tag="ML",
        prompt="""Training on a stream that is too large to shuffle in memory uses a **shuffle buffer**, as in `tf.data`: fill a
        buffer with the first `size` items; then, for every new item, pick a random position in the buffer, yield the item there
        and put the new item in its place; at the end, yield the remaining buffer in random order. Write a generator
        `shuffled(iterable, size, seed)` using `random.Random(seed)`.""",
        code="""
        import random

        def shuffled(iterable, size, seed):
            pass
        """,
        tests="""
        data = list(range(100))
        out = list(shuffled(iter(data), size=10, seed=0))
        assert sorted(out) == data and out != data
        assert all(v <= j + 9 for j, v in enumerate(out))
        assert list(shuffled(data, 1, seed=3)) == data
        assert list(shuffled(data, 10, seed=7)) == list(shuffled(data, 10, seed=7))
        assert list(shuffled([], 5, seed=0)) == []
        assert sorted(shuffled("abc", 10, seed=1)) == ["a", "b", "c"]
        """,
        hints=["`rng = random.Random(seed)` gives a private, reproducible random generator. `rng.randrange(len(buffer))` picks a position.",
               "While the buffer is not full, just append. After that, swap: `out, buffer[i] = buffer[i], item`, then yield `out`. At the end, `rng.shuffle(buffer)` and `yield from buffer`."],
        solution="""
        import random

        def shuffled(iterable, size, seed):
            rng = random.Random(seed)
            buffer = []
            for item in iterable:
                if len(buffer) < size:
                    buffer.append(item)
                    continue
                i = rng.randrange(size)
                out, buffer[i] = buffer[i], item
                yield out
            rng.shuffle(buffer)
            yield from buffer
        """,
        why="""The buffer bounds memory at `size` items whatever the stream length, and each output is drawn from a window of the stream,
        which is what the `v <= j + 9` test checks: item `v` can only be output once it has entered the buffer, so it never appears
        more than `size - 1` positions earlier than its original place. That also shows the limit of the technique: a small buffer
        gives a locally shuffled stream, so data sorted by label stays mostly sorted; real pipelines shuffle the file order too, or
        use a buffer much larger than the runs of similar items. A private `random.Random(seed)` makes the order reproducible
        without touching the global random state, which matters for repeatable experiments. With `size=1`, each item is swapped
        straight out, so the order is unchanged."""),
    predict("Closing, finally and return values", "hard",
        code="""
        def worker():
            try:
                yield "step 1"
                yield "step 2"
            finally:
                print("cleanup")

        g = worker()
        print(next(g))
        g.close()
        print("closed", next(g, "nothing"))

        def inner():
            yield 1
            return "inner result"

        def outer():
            r = yield from inner()
            yield r.upper()

        print(list(outer()))
        g2 = inner()
        print(next(g2))
        try:
            next(g2)
        except StopIteration as e:
            print("value", e.value)
        """,
        hints=["`close()` raises `GeneratorExit` at the paused `yield`, so `finally` runs. A closed generator is exhausted.",
               "A generator's `return` value travels on the `StopIteration` it raises, as `e.value`."],
        why="""`close` runs the `finally` block at once ("cleanup"), and a closed generator behaves as exhausted, so `next(g, "nothing")`
        returns the default. In `outer`, `yield from` passes the 1 through and then receives the inner `return` value, which is
        yielded upper-cased. Driving `inner` by hand shows the mechanism: the first `next` returns 1, the second finds the body
        finished, and the `return` value arrives as the `value` attribute of the `StopIteration`. A `for` loop discards that value,
        which is why `yield from` is the normal way to receive it."""),
)

section("interview", "Interview questions",
    explain("What is the difference between an iterable, an iterator and a generator?", "medium", tag="Interview",
        why="""An **iterable** is any object you can loop over; it has `__iter__`, which returns an iterator. Lists, dicts, strings,
        files and ranges are iterables. An **iterator** is the object that does the walking: it has `__next__`, which returns the
        next value or raises `StopIteration`, and `__iter__` returning itself. Iterators are one-shot and stateful; iterables such as
        lists can produce a fresh iterator every time. A **generator** is a convenient way to write an iterator: a function with
        `yield` (or a generator expression) whose local state is kept between `next` calls, so you do not have to write a class with
        `__next__` by hand. Every generator is an iterator; not every iterator is a generator (`zip`, `map` and file objects are
        iterators implemented in C)."""),
    explain("When would you use a generator instead of returning a list, and what do you give up?", "medium", tag="Interview",
        why="""Use a generator when the data is large or unbounded (files, database cursors, streams, infinite sequences), when the
        consumer may stop early (searching for the first match, taking the first N), when you want to start processing before all
        data exists (streaming model output to a user), or when you are building a pipeline of steps. You gain constant memory and
        lower latency to the first item. You give up random access and `len`, the ability to iterate twice (a generator is
        one-shot), and easy debugging (printing the generator shows nothing useful). Errors also move: they happen when values are
        consumed, not when the function is called. If the result is small and used several times, a list is simpler."""),
    explain("How would you stream an LLM reply from the model API through your backend to a browser?", "hard", tag="Interview",
        why="""Call the model with streaming enabled, which gives an iterator (or async iterator) of events. Wrap it in a generator in the
        backend that extracts each text delta and yields it, optionally formatted as server-sent events (`data: ...\\n\\n`), and pass
        that generator to the framework's streaming response (FastAPI's `StreamingResponse`, ideally with an async generator so one
        slow client does not block a worker). The browser reads the stream with `EventSource` or `fetch` and appends text as it
        arrives. Details that matter in production: collect the full text and usage counts in the generator for logging, in a
        `finally` block so they are recorded even if the stream ends early; handle client disconnects, where the framework closes the
        generator and you should cancel the upstream request so you stop paying for tokens; send an error event if the model fails
        mid-stream, because the HTTP status code was already sent; make sure no proxy buffers the response; and run moderation or
        output checks either on the stream in chunks or accept that some text was shown before the check."""),
)

recap(
    "A `for` loop calls `iter()` once and `next()` until `StopIteration`. Lists can be walked many times; iterators, generators, `zip` and files only once.",
    "A function with `yield` returns a generator; its body runs only on `next`, pauses at each `yield` and keeps its locals.",
    "`(expr for x in xs)` is lazy and tiny in memory; its first iterable is captured at creation, the rest is evaluated on demand.",
    "`yield from` delegates and receives the inner `return` value; `close()` and early `break` run the generator's `finally` blocks.",
    "Traps: second passes see nothing, argument checks run late (validate in a wrapper), and a generator returned from inside `with` reads a closed file.",
)
