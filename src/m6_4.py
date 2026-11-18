from lesson import *
from diagrams import *

lesson(
    id="m6-4", num="6.4", title="Lazy pipelines",
    intro="Chain generators into pipelines that process one item at a time, and use the `itertools` toolkit: taking and "
          "skipping, combining streams, running totals, batching, `groupby` and its sorting trap, combinatorics, and what "
          "breaks laziness. Applied to log processing, context packing, hyperparameter grids and an embedding pipeline.",
    desc="Generator pipelines and `itertools`: `islice`, `chain`, `accumulate`, `batched`, `groupby`, `product`.",
    keys="pipeline lazy itertools islice count chain zip_longest pairwise accumulate batched takewhile dropwhile groupby product combinations permutations tee heapq merge stream etl embedding grid search",
)

term("Pipeline", "A chain of steps where each step takes an iterable and yields results to the next. With generators, items flow through one at a time.")
term("itertools", "A standard-library module of fast iterator building blocks: `islice`, `chain`, `accumulate`, `batched`, `groupby`, `product` and more.")
term("Consecutive grouping", "What `itertools.groupby` does: it groups runs of adjacent items with the same key, so data must be sorted by that key first.")

section("pipeline", "Building a pipeline from generators",
    fig(chain(["read lines", "strip, skip blanks", "parse JSON", "keep valid", "batch(32)", ("embed", "accent")],
        note="each item flows through every stage before the next line is read"),
        "A lazy pipeline: chained generators, where only one item (or one batch) is in memory at a time."),
    p("""A **pipeline** is a chain of steps where each step takes an iterable and returns a new iterable. When every step is a
    generator, the whole chain is **lazy**: building it does no work at all, and when the consumer at the end asks for one item,
    that request travels back up the chain, each step pulls just enough from the step before it, and one item flows all the way
    through. Then the next. Only one item is "in flight" at a time, so memory stays constant however long the input is."""),
    ex("""
    def read(lines):
        for line in lines:
            print(f"  read   {line!r}")
            yield line

    def clean(rows):
        for row in rows:
            if row.strip():
                yield row.strip().lower()

    def tag(rows):
        for row in rows:
            yield f"[{len(row)}] {row}"

    pipeline = tag(clean(read(["Refund ", "", "RESET"])))
    print("built, nothing read yet")
    for out in pipeline:
        print(out)
    """, "pipeline.py"),
    p("""The output shows the interleaving: "read" for the first line, then its tagged result, then the next read. Each line is read,
    cleaned and tagged before the next one is read; the empty line is read and dropped by `clean`, so nothing is printed for it
    downstream. This is the same idea as a database query plan or Power Query's lazy evaluation: you describe the steps, and the
    engine streams rows through them when the result is requested."""),
    p("""Generator expressions make one-line steps: `stripped = (l.strip() for l in lines)`, `nonempty = (l for l in stripped if
    l)`. Generator functions are for steps with state or several statements, such as deduplication, parsing with error handling or
    batching. A useful rule: each step should do one job and be testable alone with a list as input."""),
    callout("sql", "SQL / Power BI", """A pipeline is like a query written as a chain of CTEs: `WITH cleaned AS (...), tagged AS (...)
    SELECT ...`. In both, the steps describe a flow of rows, and the engine decides when rows move. Power Query's query folding and
    streaming are the same principle: nothing is evaluated until the result is needed, and steps like sorting force the engine to
    read everything first."""),
)

section("take", "Taking, skipping and stopping",
    p("""Generators cannot be sliced with `[a:b]`, because their items do not exist yet. **`itertools.islice(iterable, stop)`** or
    `islice(iterable, start, stop, step)` is the lazy slice: it skips and takes items by position as they stream past, and stops
    pulling from the source as soon as it has what it needs. It is how you take the first `n` items of a stream, skip a header,
    or sample every 10th record. Negative indices are not allowed, since a stream's end is not known in advance."""),
    ex("""
    from itertools import islice, count, takewhile, dropwhile

    print(list(islice(count(1), 5)), list(islice("abcdefgh", 2, 7, 2)))
    lines = iter(["id,text", "1,refund", "2,reset", "3,invoice"])
    header = next(lines)
    print(header, list(islice(lines, 2)), list(lines))
    scores = [0.95, 0.91, 0.88, 0.42, 0.93]
    print(list(takewhile(lambda s: s > 0.8, scores)), list(dropwhile(lambda s: s > 0.8, scores)))
    """, "take_skip.py"),
    p("""`count(start)` is an infinite counter, safe because `islice` stops it. Notice how the file-like iterator is shared: `next`
    took the header, `islice` took the next two lines, and `list(lines)` got what was left, the one-shot behaviour of 6.3 put to
    good use. **`takewhile(pred, it)`** yields items while the predicate is true and stops **for good** at the first false one;
    **`dropwhile(pred, it)`** skips items while the predicate is true and then yields **everything** after, including later items
    that would fail the predicate (like `0.93` above). They act on a prefix of the stream, unlike `filter`, which tests every
    item."""),
)

section("combine", "Combining and reshaping streams",
    p("""Several tools combine or reshape iterables lazily. **`chain(a, b, ...)`** yields all of `a`, then all of `b`, without building
    a combined list; `chain.from_iterable(iterable_of_iterables)` does the same for a stream of streams, which is the lazy version
    of flattening (6.1). **`zip_longest`** pairs items like `zip` but continues to the longest input, filling gaps with
    `fillvalue`, where `zip` would silently stop at the shortest (4.1). **`pairwise`** (Python 3.10+) yields overlapping pairs of
    neighbours, `(a, b), (b, c), ...`, which is how you compute differences between consecutive values. **`batched(it, n)`**
    (Python 3.12+) yields tuples of `n` items, the last one shorter."""),
    ex("""
    from itertools import chain, zip_longest, pairwise, batched

    print(list(chain([1, 2], (3,), "ab")), list(chain.from_iterable([[1], [], [2, 3]])))
    print(list(zip_longest("abc", [1], fillvalue=None)))
    timestamps = [100, 103, 110, 111]
    print([b - a for a, b in pairwise(timestamps)])
    print(list(batched(range(7), 3)))
    """, "combine.py"),
    p("""**`accumulate(it, func=operator.add, initial=None)`** yields running results: running totals by default, or running maxima,
    products or anything else with another two-argument function. Running token totals are a common use in GenAI code, to know
    where a context budget runs out (problem 5)."""),
    ex("""
    from itertools import accumulate, takewhile
    import operator

    tokens = [120, 300, 80, 500, 60]
    print(list(accumulate(tokens)), list(accumulate(tokens, max)), list(accumulate([2, 3, 4], operator.mul)))
    budget = 520
    fits = sum(1 for total in takewhile(lambda t: t <= budget, accumulate(tokens)))
    print(fits, tokens[:fits])
    """, "accumulate.py"),
    p("""The last two lines combine two lazy tools: `accumulate` produces the running totals and `takewhile` stops at the first total
    over budget, so the stream of chunks is never read further than needed. `map(func, it)` and `filter(pred, it)` are the
    built-in lazy transform and filter, and `zip` is lazy too; all of them compose into pipelines."""),
)

section("groupby", "`groupby`: grouping a sorted stream",
    fig(table(["input to groupby", "groups produced"], [["a a b b a", "a, b, a  (three groups)"], ["sorted: a a a b b", "a, b  (two groups)"]],
        hl={(0, 1)}, label="groupby groups consecutive items"),
        "`itertools.groupby` groups runs of equal keys, so sort by the same key first, or use a dict when order does not matter."),
    p("""`itertools.groupby(iterable, key)` yields pairs `(key, group)` for **runs of consecutive items** that have the same key.
    That is different from SQL's `GROUP BY`: it does not collect all items with the same key from anywhere in the input, it only
    groups items that are **next to each other**. On unsorted data, the same key appears several times. So the standard pattern
    is to sort by the same key first, then group."""),
    ex("""
    from itertools import groupby

    logs = [("auth", 30), ("rag", 120), ("auth", 50), ("rag", 340), ("rag", 200)]
    print([(k, len(list(g))) for k, g in groupby(logs, key=lambda r: r[0])])
    by_service = sorted(logs, key=lambda r: r[0])
    print([(k, [ms for _, ms in g]) for k, g in groupby(by_service, key=lambda r: r[0])])
    print([(k, len(list(g))) for k, g in groupby("aaabccaa")])
    """, "groupby.py"),
    p("""The consecutive behaviour is not only a trap; it is useful on its own. Run-length encoding (`aaabccaa` gives a run of `a`, then
    `b`, then `c`, then `a` again) and splitting a time-ordered log into blocks of the same status are both "group consecutive
    items", and they work on a stream without sorting. Sorting, on the other hand, reads the whole input into memory, so `sorted`
    followed by `groupby` is not a lazy pipeline; for data that is already sorted by the key (a database export ordered by
    customer, a file sorted by date), `groupby` streams."""),
    p("""The second trap: each `group` is an iterator that **shares** the underlying stream with `groupby` itself. When `groupby`
    moves on to the next key, the previous group's iterator is exhausted. So `list(groupby(...))` gives you keys with empty
    groups; consume or copy each group (`list(g)`) inside the loop, before moving on (problem 12)."""),
    ex("""
    from itertools import groupby

    data = sorted(["refund", "reset", "invoice", "rate"], key=len)
    saved = list(groupby(data, key=len))
    print([(k, list(g)) for k, g in saved])
    print([(k, list(g)) for k, g in groupby(data, key=len)])
    """, "groupby_trap.py"),
)

section("combinatorics", "Combinatorics: product, combinations, permutations",
    p("""Three tools generate arrangements lazily, which matters because their output grows very fast. **`product(a, b, ...)`** is the
    Cartesian product, every combination of one item from each input, the same as nested `for` loops (6.1); `product(xs,
    repeat=2)` pairs `xs` with itself. **`combinations(xs, r)`** yields every unordered selection of `r` distinct positions, in
    order, without repeats: all pairs of documents to compare, for example, `n * (n - 1) / 2` of them. **`permutations(xs, r)`**
    yields every ordered arrangement."""),
    ex("""
    from itertools import product, combinations, permutations
    from math import comb

    print(list(product([0.1, 0.01], [16, 32])))
    print(list(combinations("abc", 2)), list(permutations("abc", 2))[:4])
    print(comb(10_000, 2), sum(1 for _ in combinations(range(200), 2)) == comb(200, 2))
    """, "combinatorics.py"),
    p("""`product` is the core of **grid search** over hyperparameters: every combination of learning rates, batch sizes and so on,
    which is what scikit-learn's `ParameterGrid` produces (problem 7). `combinations` is the naive way to compare all pairs, such
    as finding near-duplicate documents, and `math.comb` shows why it does not scale: 10,000 documents already give 50 million
    pairs, which is why real deduplication uses hashing techniques (MinHash, or exact hashes for exact duplicates) instead of
    comparing everything with everything (problem 11)."""),
)

section("breaks", "What breaks laziness, and splitting a stream",
    fig(chain(["a generator", "list(...), sorted(...),|len(list(...))", ("the whole stream|is now in memory", "bad")]),
        "Anything that needs all items at once ends the laziness; keep such steps for the end, or for data you know is small."),
    p("""Some operations need **all** the data before they can produce anything, and putting one in a pipeline turns everything
    before it into a full read: `sorted`, `reversed` (which needs a sequence), `len`, `list`, `set`, `max` and `min` (which return
    after reading everything, though in constant memory), and the `sorted`-then-`groupby` pattern. That is not wrong; it just
    has to be a conscious decision. Keep such steps at the end, or make them work on bounded data (the top-k with a heap from 4.2,
    for example, keeps only `k` items while streaming)."""),
    p("""Sometimes you need to consume one stream in two ways. **`itertools.tee(it, n)`** returns `n` independent iterators over the
    same stream, but it works by **buffering** every item that one copy has seen and the other has not yet. If one copy runs far
    ahead of the other, the buffer grows to hold the gap, up to the whole stream. Use `tee` when the copies advance roughly
    together (looking one item ahead, for example); when one would be consumed completely before the other, a list is simpler
    and uses the same memory."""),
    ex("""
    from itertools import tee, islice
    import heapq

    stream = (n * n for n in range(10))
    a, b = tee(stream)
    print(list(islice(a, 3)), list(islice(b, 5)))
    scores = (s % 97 for s in range(1_000_000))      # a stream of a million scores
    print(heapq.nlargest(3, scores))                  # keeps only 3 items while streaming
    """, "tee_and_topk.py"),
    p("""Finally, merging several **sorted** streams into one sorted stream does not require sorting at all: `heapq.merge(*streams,
    key=...)` keeps one item per stream in a small heap and always yields the smallest, which is how log files from several
    servers, each sorted by time, are combined into one timeline lazily (problem 15)."""),
)

section("practice", "Pipelines in practice",
    p("""Real data pipelines are these pieces in a row. A typical **embedding ingestion** job reads a large JSON Lines file, parses and
    validates records, normalises text, drops duplicates, batches the texts to the embedding API's limit, calls the API per batch
    and writes the vectors out, and each step is a small generator or itertools call. Because everything is lazy, the job starts
    producing results immediately, uses constant memory, and can be stopped and resumed (with `islice` to skip what was done)."""),
    ex("""
    import hashlib, json
    from itertools import batched, islice

    def parse(lines):
        for line in lines:
            if line.strip():
                yield json.loads(line)

    def unique(records):
        seen = set()
        for r in records:
            h = hashlib.sha256(r["text"].strip().lower().encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                yield r

    def fake_embed(texts):
        return [[len(t), t.count(" ")] for t in texts]

    lines = ['{"id": 1, "text": "Refund policy"}', '{"id": 2, "text": "refund policy "}', "",
             '{"id": 3, "text": "Reset password"}', '{"id": 4, "text": "Invoice copy"}']
    for batch in batched(unique(parse(lines)), 2):
        vectors = fake_embed([r["text"] for r in batch])
        print([r["id"] for r in batch], vectors)
    print(list(islice(unique(parse(lines)), 1, None)))
    """, "embedding_pipeline.py"),
    p("""The `seen` set of hashes is the one piece of state that grows, one 64-character hash per unique text rather than the texts
    themselves. Swapping `fake_embed` for a real API call (with retries and rate limits, Module 12) is the only change needed for
    production. This is the structure you would also implement in pandas chunks, Polars' streaming engine, or a Spark job when
    one machine is not enough: the same steps, each a lazy transformation of a stream of rows."""),
)

section("warmup", "Warm-up",
    predict("The itertools toolkit", "easy",
        code="""
        from itertools import islice, count, chain, pairwise, accumulate, batched

        print(list(islice(count(10, 5), 3)), list(islice("pipeline", 4)))
        print(list(chain("ab", [1])), [b - a for a, b in pairwise([3, 7, 8])])
        print(list(accumulate([1, 2, 3, 4])), list(batched("abcde", 2)))
        """,
        hints=["`count(10, 5)` counts from 10 in steps of 5. `pairwise` yields neighbours; `accumulate` running totals; `batched` tuples."],
        why="""`islice` takes the first three values of the infinite counter, and the first four characters of the string. `chain` joins
        iterables of any kind. The `pairwise` differences are 7 - 3 and 8 - 7. `accumulate` gives running totals, and `batched`
        gives tuples, the last one shorter."""),
    write("Skip the header, take n rows", "easy", tag="Data work",
        prompt="""Write `preview(lines, n, header=True)` returning a list of the first `n` data rows of a CSV given as an iterable
        of lines (a file, a list), each split on commas and stripped. If `header` is true, skip the first line. Read no more
        lines than needed: it must work on a huge or infinite stream.""",
        code="""
        from itertools import islice

        def preview(lines, n, header=True):
            pass
        """,
        tests="""
        rows = ["id,text\\n", "1, refund\\n", "2,reset \\n", "3,invoice\\n"]
        assert preview(rows, 2) == [["1", "refund"], ["2", "reset"]]
        assert preview(rows, 2, header=False) == [["id", "text"], ["1", "refund"]]
        assert preview(rows, 10) == [["1", "refund"], ["2", "reset"], ["3", "invoice"]]

        def endless():
            yield "a,b"
            i = 0
            while True:
                i += 1
                yield f"{i},x"
        assert preview(endless(), 3) == [["1", "x"], ["2", "x"], ["3", "x"]]
        """,
        hints=["`islice(lines, 1, 1 + n)` skips one line and takes `n`; `islice(lines, n)` takes `n`."],
        solution="""
        from itertools import islice

        def preview(lines, n, header=True):
            start = 1 if header else 0
            return [[cell.strip() for cell in line.split(",")] for line in islice(lines, start, start + n)]
        """,
        why="""`islice` with a start and stop skips the header and takes exactly `n` lines, then stops pulling, which is what makes the
        infinite stream safe. Asking for more rows than exist just returns what there is. A comprehension around it does the
        splitting, and since `islice` is lazy, only the needed lines are ever split. (For real CSV with quoted commas, use the
        `csv` module; it works on the same kind of line iterable.)"""),
    fix("groupby splits the same service into several groups", "easy", tag="Data work",
        prompt="""`latency_by_service(logs)` should return `{service: total_ms}`. With unsorted logs, totals are wrong: some
        services lose most of their time. Fix it, keeping `groupby`.""",
        code="""
        from itertools import groupby

        def latency_by_service(logs):
            return {svc: sum(ms for _, ms in g) for svc, g in groupby(logs, key=lambda r: r[0])}
        """,
        tests="""
        logs = [("auth", 30), ("rag", 120), ("auth", 50), ("rag", 340), ("rag", 200), ("db", 5)]
        assert latency_by_service(logs) == {"auth": 80, "db": 5, "rag": 660}
        assert latency_by_service([]) == {}
        """,
        hints=["`groupby` only groups **consecutive** items. Sort by the same key first."],
        solution="""
        from itertools import groupby

        def by_service(r):
            return r[0]

        def latency_by_service(logs):
            ordered = sorted(logs, key=by_service)
            return {svc: sum(ms for _, ms in g) for svc, g in groupby(ordered, key=by_service)}
        """,
        why="""Unsorted, `auth` appears in two separate runs, and each run became its own group; the dict comprehension then assigned
        `auth` twice and the **last** run's total won (6.2), losing the first. Sorting by the same key function makes all records
        of a service adjacent, so each key forms exactly one run. Naming the key function once guarantees that the sort and the
        grouping use the same key. Without the need for a lazy stream, a `defaultdict(int)` in one pass (4.6) is simpler and
        avoids the sort."""),
    predict("Who runs when in a pipeline", "easy",
        code="""
        def numbers():
            for n in [1, 2, 3]:
                print("make", n)
                yield n

        def double(xs):
            for x in xs:
                print("double", x)
                yield x * 2

        p = double(numbers())
        print("first:", next(p))
        print("rest:", list(p))
        """,
        hints=["Each `next` at the end pulls one item through the whole chain."],
        why="""Building `p` runs nothing. `next(p)` asks `double` for an item, which asks `numbers`, which prints "make 1" and yields;
        then `double` prints "double 1" and yields 2. `list(p)` repeats that for the remaining items, one at a time, so "make" and
        "double" alternate. Only after the whole chain is exhausted does `print` receive the list and print "rest:"."""),
)

section("medium", "Medium",
    write("Pack chunks into a token budget", "medium", tag="RAG",
        prompt="""A prompt has room for `budget` tokens of context. Write `pack(chunks, budget)` that takes chunks **in ranked
        order** from any iterable and returns the list of chunks that fit, stopping at the first chunk that would exceed the
        budget (do not skip it to try smaller later ones). Approximate tokens as `len(text.split())`. Use `accumulate` and
        `takewhile`, and read no further than needed.""",
        code="""
        from itertools import accumulate, takewhile

        def pack(chunks, budget):
            pass
        """,
        tests="""
        chunks = ["Refunds take five days.", "No refunds after thirty days from purchase.", "Contact support.", "x " * 50]
        assert pack(chunks, 10) == ["Refunds take five days."]
        assert pack(chunks, 11) == ["Refunds take five days.", "No refunds after thirty days from purchase."]
        assert pack(chunks, 3) == []
        assert pack([], 100) == []

        read = []
        def ranked():
            for c in chunks:
                read.append(c)
                yield c
        pack(ranked(), 11)
        assert len(read) == 3
        """,
        hints=["Pair each chunk with the running total: `zip(chunks, accumulate(...))` needs the chunks twice, so first make pairs of `(chunk, tokens)` in one generator.",
               "`accumulate` over the token counts, then `takewhile(lambda pair: pair[1] <= budget, ...)` over `(chunk, running_total)` pairs."],
        solution="""
        from itertools import accumulate, takewhile

        def pack(chunks, budget):
            sized = ((c, len(c.split())) for c in chunks)
            running = accumulate(sized, lambda acc, item: (item[0], acc[1] + item[1]))
            return [c for c, total in takewhile(lambda pair: pair[1] <= budget, running)]
        """,
        why="""`accumulate` works with any two-argument function, so it can carry a pair: the current chunk and the running token total.
        The first pair passes through as it is, and each later step keeps the new chunk and adds its size to the total. `takewhile`
        stops at the first total over budget, and since everything is lazy, the source is read only one item past the last chunk
        that fits, which the `read` test checks. Stopping at the first chunk that does not fit, rather than skipping it, keeps the
        context in rank order, the usual choice; packing smaller lower-ranked chunks into the gap is a different policy (a knapsack
        heuristic). Real code counts tokens with the model's tokenizer, not `split`."""),
    fix("Differences between readings from a stream", "medium", tag="Data work",
        prompt="""`deltas(readings)` returns the differences between consecutive readings. It works on lists but fails on
        generators and other iterators with `TypeError`. Fix it so it works on any iterable, lazily, yielding the differences.""",
        code="""
        def deltas(readings):
            return [b - a for a, b in zip(readings, readings[1:])]
        """,
        tests="""
        assert list(deltas([100, 103, 110, 111])) == [3, 7, 1]
        assert list(deltas(t for t in [5, 5, 9])) == [0, 4]
        assert list(deltas([42])) == [] and list(deltas([])) == []
        import inspect
        assert not isinstance(deltas([1, 2]), list)
        """,
        hints=["`readings[1:]` needs a sequence. `itertools.pairwise` yields neighbours from any iterable."],
        solution="""
        from itertools import pairwise

        def deltas(readings):
            return (b - a for a, b in pairwise(readings))
        """,
        why="""Slicing needs a sequence, so `readings[1:]` raised `TypeError: 'generator' object is not subscriptable`. On a list, the slice
        also copied every item. `pairwise` keeps only the previous item while streaming, works on any iterable, and returns
        nothing for fewer than two items. Returning a generator expression keeps the function lazy, which the last test checks.
        Before Python 3.10 the same thing was written with `tee`: two copies of the iterator, one advanced by one step, zipped
        together."""),
    write("A hyperparameter grid", "medium", tag="ML",
        prompt="""Write `grid(space)` where `space` maps parameter names to lists of values. Return a list of dicts, one per
        combination, like scikit-learn's `ParameterGrid`, varying the **last** parameter fastest. Parameters keep the order of
        `space`. An empty space gives one empty dict; a parameter with no values gives no combinations.""",
        code="""
        from itertools import product

        def grid(space):
            pass
        """,
        tests="""
        space = {"lr": [0.1, 0.01], "depth": [3, 5], "loss": ["log"]}
        assert grid(space) == [
            {"lr": 0.1, "depth": 3, "loss": "log"}, {"lr": 0.1, "depth": 5, "loss": "log"},
            {"lr": 0.01, "depth": 3, "loss": "log"}, {"lr": 0.01, "depth": 5, "loss": "log"},
        ]
        assert grid({}) == [{}]
        assert grid({"a": [1], "b": []}) == []
        assert len(grid({"a": range(3), "b": range(4), "c": range(5)})) == 60
        """,
        hints=["`product(*space.values())` gives tuples of values in key order. `dict(zip(space, values))` names them."],
        solution="""
        from itertools import product

        def grid(space):
            names = list(space)
            return [dict(zip(names, values)) for values in product(*space.values())]
        """,
        why="""Unpacking the value lists into `product` gives every combination, with the last list varying fastest, exactly like nested
        loops (6.1). `zip` with the key list names each tuple. The edge cases come out right on their own: `product()` with no
        arguments yields one empty tuple, hence `[{}]`, and any empty list makes the product empty. The grid grows as the product of
        the list sizes (60 here), which is why large searches use random search or Bayesian optimisation (Optuna) instead of
        trying every combination."""),
    choose("The first 10 records: parse all or slice the stream", "medium",
        prompt="Both return the first 10 parsed records from 200,000 JSON lines. Which is faster?",
        setup="""import json
from itertools import islice
lines = ['{"id": %d, "text": "refund request", "score": 0.5}' % i for i in range(200_000)]""",
        options={
            "a": "rows = [json.loads(line) for line in lines][:10]",
            "b": "rows = list(islice((json.loads(line) for line in lines), 10))",
        },
        answer="b",
        hints=["How many lines does each version parse?"],
        why="""The list comprehension parses all 200,000 lines, the expensive part, and then keeps ten. `islice` over a generator
        expression parses exactly ten and stops. Laziness pays off most when each item is expensive (parsing, a regex, an API
        call) and you need only some of them: previews, sampling, "first match" searches. When all items are needed anyway, the
        two cost the same."""),
    trace("itertools results", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        from itertools import islice, count, chain, zip_longest, accumulate, groupby, dropwhile
        r = list(islice(count(5), 3))  # row: "islice of count"
        r = list(chain(r, "ab"))  # row: "chain"
        r = list(zip_longest("ab", [1], fillvalue=0))  # row: "zip_longest"
        r = list(accumulate([3, 1, 4, 1], max))  # row: "running max"
        r = [(k, len(list(g))) for k, g in groupby("aaabba")]  # row: "groupby runs"
        r = list(dropwhile(lambda x: x < 3, [1, 2, 5, 1, 7]))  # row: "dropwhile"
        """,
        trace_vars=["r"],
        hints=["`groupby` groups consecutive runs only. `dropwhile` drops a prefix and then keeps everything."],
        why="""`count(5)` starts at 5. `chain` appends the characters of `"ab"`. `zip_longest` pads the shorter input with the fill value.
        A running maximum never decreases. `groupby` sees three runs, with `a` appearing twice because its runs are not adjacent.
        `dropwhile` drops 1 and 2, then yields 5 and everything after it, including the 1 that would have failed the test."""),
    write("Split an event stream into sessions", "medium", tag="ML",
        prompt="""Feature pipelines often group user events into **sessions**: a new session starts when the gap since the previous
        event is more than `gap` seconds. Write a generator `sessions(events, gap)` that takes `(timestamp, action)` pairs
        sorted by time and yields each session as a list of actions, lazily: a session is yielded as soon as the next event
        shows it is over.""",
        code="""
        def sessions(events, gap):
            pass
        """,
        tests="""
        events = [(0, "open"), (20, "search"), (50, "click"), (400, "open"), (410, "buy"), (2000, "open")]
        assert list(sessions(events, 60)) == [["open", "search", "click"], ["open", "buy"], ["open"]]
        assert list(sessions(events, 10_000)) == [["open", "search", "click", "open", "buy", "open"]]
        assert list(sessions([], 60)) == []
        g = sessions(iter(events), 60)
        assert next(g) == ["open", "search", "click"]
        """,
        hints=["Keep the current session and the previous timestamp. When the gap is too big, yield the current session and start a new one.",
               "After the loop, yield the last session if it is not empty."],
        solution="""
        def sessions(events, gap):
            current, last = [], None
            for ts, action in events:
                if last is not None and ts - last > gap:
                    yield current
                    current = []
                current.append(action)
                last = ts
            if current:
                yield current
        """,
        why="""A session's end is only known when the next event arrives, so the generator yields the finished session at that moment and
        starts a new one; the last session is yielded after the loop, when the stream ends. Memory holds only the current session,
        not the whole history, so this runs on a live event stream. Using `None` for "no previous event" keeps the first event from
        being compared with anything. The same shape (accumulate until a boundary, then yield) is used for sentences, paragraphs and
        conversation turns. In pandas this is `(df.ts.diff() > gap).cumsum()` used as a group key."""),
    refactor("All pairs with combinations", "medium", tag="ML",
        prompt="Rewrite the nested index loops with `itertools.combinations`, same result. Keep the tests green.",
        code="""
        def near_duplicates(docs, threshold):
            ids = list(docs)
            words = [set(docs[i].lower().split()) for i in ids]
            pairs = []
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    a, b = words[i], words[j]
                    if a or b:
                        score = len(a & b) / len(a | b)
                        if score >= threshold:
                            pairs.append((ids[i], ids[j], round(score, 2)))
            return pairs
        """,
        tests="""
        docs = {"d1": "refund policy for EU", "d2": "Refund policy for the EU", "d3": "reset your password", "d4": ""}
        assert near_duplicates(docs, 0.5) == [("d1", "d2", 0.8)]
        assert near_duplicates(docs, 0.0) == [("d1", "d2", 0.8), ("d1", "d3", 0.0), ("d1", "d4", 0.0), ("d2", "d3", 0.0),
                                              ("d2", "d4", 0.0), ("d3", "d4", 0.0)]
        assert near_duplicates({}, 0.1) == []
        """,
        hints=["`combinations(docs.items(), 2)` yields each unordered pair once, in the same order as the index loops."],
        solution="""
        from itertools import combinations

        def jaccard(a, b):
            return len(a & b) / len(a | b) if a or b else None

        def near_duplicates(docs, threshold):
            words = {doc_id: set(text.lower().split()) for doc_id, text in docs.items()}
            pairs = []
            for (id_a, a), (id_b, b) in combinations(words.items(), 2):
                score = jaccard(a, b)
                if score is not None and score >= threshold:
                    pairs.append((id_a, id_b, round(score, 2)))
            return pairs
        """,
        why="""`combinations(items, 2)` yields every pair `(i, j)` with `i` before `j`, which is exactly what the `range(i + 1, ...)` loop
        built by hand, without the index bookkeeping. Unpacking each pair into `(id, words)` tuples replaces the parallel `ids` and
        `words` lists. The similarity moves into a named function, where "both empty" is handled explicitly. The number of pairs
        still grows with the square of the number of documents; the refactor makes the code clearer, not cheaper. At scale, MinHash
        with locality-sensitive hashing (the `datasketch` library) finds near-duplicate pairs without comparing all of them."""),
    fix("Grouped results that come back empty", "medium", tag="RAG",
        prompt="""`by_source(results)` groups retrieval results by source document, keeping the order of the results within each
        source. Every group comes back empty. Fix it.""",
        code="""
        from itertools import groupby

        def by_source(results):
            ordered = sorted(results, key=lambda r: r["source"])
            groups = list(groupby(ordered, key=lambda r: r["source"]))
            return {source: [r["text"] for r in group] for source, group in groups}
        """,
        tests="""
        results = [{"source": "faq", "text": "a"}, {"source": "terms", "text": "b"}, {"source": "faq", "text": "c"}]
        assert by_source(results) == {"faq": ["a", "c"], "terms": ["b"]}
        assert by_source([]) == {}
        """,
        hints=["Each group is an iterator over the shared stream. `list(groupby(...))` moves past every group before you read any of them."],
        solution="""
        from itertools import groupby

        def by_source(results):
            ordered = sorted(results, key=lambda r: r["source"])
            return {source: [r["text"] for r in group] for source, group in groupby(ordered, key=lambda r: r["source"])}
        """,
        why="""`groupby` produces each group lazily from the same underlying iterator. `list(groupby(...))` runs `groupby` to the end,
        advancing past every item, so each saved group iterator is already exhausted when it is read. Consuming each group as soon as
        it is produced, inside the same loop, fixes it. `sorted` is stable (4.2), so results from the same source stay in their
        original order, which matters when they are ranked. A `defaultdict(list)` would do the same without sorting."""),
)

section("hard", "Hard",
    write("An embedding ingestion pipeline", "hard", tag="RAG",
        prompt="""Write a generator `ingest(lines, embed, batch_size)` that takes JSON lines with `"id"` and `"text"`, skips blank
        lines and lines that are not valid JSON, normalises text (strip, collapse whitespace), skips records whose normalised text is
        empty or was already seen (compare case-insensitively), groups the rest into batches of `batch_size`, calls `embed(texts)`
        once per batch (it returns one vector per text), and yields `(id, vector)` pairs. It must be lazy: taking the first pair
        must call `embed` only once.""",
        code="""
        import json
        from itertools import batched

        def ingest(lines, embed, batch_size):
            pass
        """,
        tests="""
        calls = []
        def embed(texts):
            calls.append(list(texts))
            return [[len(t)] for t in texts]

        lines = ['{"id": 1, "text": "Refund  policy"}', "", "{bad json", '{"id": 2, "text": " refund policy "}',
                 '{"id": 3, "text": "Reset password"}', '{"id": 4, "text": "   "}', '{"id": 5, "text": "Invoice copy"}']
        assert list(ingest(lines, embed, 2)) == [(1, [13]), (3, [14]), (5, [12])]
        assert calls == [["Refund policy", "Reset password"], ["Invoice copy"]]

        calls.clear()
        g = ingest(iter(lines * 100), embed, 2)
        assert next(g) == (1, [13]) and len(calls) == 1
        """,
        hints=["Write small steps: `parse(lines)` yields dicts, skipping bad JSON; `clean(records)` normalises with `\" \".join(text.split())` and dedupes with a `seen` set of `casefold()`ed texts.",
               "Then `for batch in batched(clean(parse(lines)), batch_size):` call `embed([r[\"text\"] for r in batch])` and `yield from zip(ids, vectors)`."],
        solution="""
        import json
        from itertools import batched


        def _parse(lines):
            for line in lines:
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


        def _clean(records):
            seen = set()
            for r in records:
                text = " ".join(r["text"].split())
                key = text.casefold()
                if text and key not in seen:
                    seen.add(key)
                    yield r["id"], text


        def ingest(lines, embed, batch_size):
            for batch in batched(_clean(_parse(lines)), batch_size):
                ids = [i for i, _ in batch]
                vectors = embed([t for _, t in batch])
                yield from zip(ids, vectors)
        """,
        why="""Each step is a small generator with one job: `_parse` handles bad input, `_clean` normalises and deduplicates, `batched`
        sizes requests, and `ingest` calls the model and pairs ids with vectors. Because they are chained lazily, asking for the
        first pair pulls just enough lines to fill one batch, which is why `embed` is called once in the last test even though the
        input is 700 lines. Normalising before deduplicating matters: `"Refund  policy"` and `" refund policy "` are the same text
        after collapsing whitespace and case-folding, and embedding both would waste money and add near-identical vectors to the
        index. In production, the `embed` call gets retries and rate limiting, and the pairs are written to the vector store in
        batches as they come."""),
    fix("Read the code: a moving average", "hard", tag="ML",
        prompt="""This computes a moving average over a stream of latency readings, for a monitoring chart. With a list as input, it
        returns wrong values, and `k=0` crashes later with `ZeroDivisionError` instead of failing at the call. It is also slow for
        large windows. Read it, find the bugs and fix them.""",
        code="""
        from itertools import islice


        def moving_average(values, k):
            it = iter(values)
            window = list(islice(it, k))
            if len(window) < k:
                return
            yield sum(window) / k
            for v in values:
                window = window[1:] + [v]
                yield sum(window) / k
        """,
        tests="""
        assert list(moving_average([1, 2, 3, 4, 5], 2)) == [1.5, 2.5, 3.5, 4.5]
        assert list(moving_average((v for v in [1, 2, 3, 4, 5]), 3)) == [2.0, 3.0, 4.0]
        assert list(moving_average([1, 2], 3)) == []
        try:
            moving_average([1, 2], 0)
            assert False, "k=0 should raise at the call"
        except ValueError:
            pass
        """,
        hints=["The loop iterates `values`, not `it`. For a list, that starts again from the first item.",
               "A generator's checks run on the first `next` (6.3). Validate in a normal function that returns the generator.",
               "`window[1:] + [v]` and `sum(window)` cost O(k) per item. A `deque(maxlen=k)` and a running total make each step O(1)."],
        solution="""
        from collections import deque
        from itertools import islice


        def moving_average(values, k):
            if k < 1:
                raise ValueError("k must be at least 1")
            return _moving_average(values, k)


        def _moving_average(values, k):
            it = iter(values)
            window = deque(islice(it, k), maxlen=k)
            if len(window) < k:
                return
            total = sum(window)
            yield total / k
            for v in it:
                total += v - window[0]
                window.append(v)
                yield total / k
        """,
        why="""Bug one is the iterable-versus-iterator mix-up of 6.3. With a generator, `values` and `it` are the same object, so the code
        worked; with a list, `for v in values` started a new iteration from the first item, so the window re-read readings it had
        already used. Always loop over the one iterator once you have created it. Bug two: with `k=0`, the check `len(window) < k` is
        false, so the code reached `sum(window) / 0`, but only when the generator was first consumed; validating in a wrapper raises
        at the call. The performance problem: rebuilding the window and summing it is O(k) per reading. A `deque` with `maxlen`
        drops the oldest item automatically when a new one is appended, and the running total is updated by adding the new value
        and subtracting the one that leaves, so each step is O(1). (Running totals over floats slowly accumulate rounding error;
        long-running monitors recompute the sum now and then.)"""),
    write("Merge sorted log streams", "hard", tag="Data work",
        prompt="""Each server writes its own log, sorted by timestamp. Write a generator `merge_logs(*streams)` that merges any number
        of streams of `(timestamp, server, message)` tuples into one stream sorted by timestamp, lazily, without sorting: keep one
        pending item per stream in a heap with `heapq`. Ties keep the order of the streams as passed. Do not use `heapq.merge`.""",
        code="""
        import heapq

        def merge_logs(*streams):
            pass
        """,
        tests="""
        a = [(1, "a", "start"), (5, "a", "req"), (9, "a", "stop")]
        b = [(2, "b", "start"), (5, "b", "req")]
        c = []
        merged = list(merge_logs(a, b, c))
        assert [(t, s) for t, s, _ in merged] == [(1, "a"), (2, "b"), (5, "a"), (5, "b"), (9, "a")]
        assert list(merge_logs()) == []

        def ticks(server, start, step):
            t = start
            while True:
                yield (t, server, "tick")
                t += step
        g = merge_logs(ticks("x", 0, 3), ticks("y", 1, 2))
        assert [next(g)[:2] for _ in range(6)] == [(0, "x"), (1, "y"), (3, "x"), (3, "y"), (5, "y"), (6, "x")]
        """,
        hints=["Push `(timestamp, stream_index, item, iterator)` for the first item of each stream. The index breaks ties and keeps the iterator from ever being compared.",
               "Pop the smallest, yield its item, then push the next item from the same iterator if there is one."],
        solution="""
        import heapq

        def merge_logs(*streams):
            heap = []
            for index, stream in enumerate(streams):
                it = iter(stream)
                first = next(it, None)
                if first is not None:
                    heap.append((first[0], index, first, it))
            heapq.heapify(heap)
            while heap:
                ts, index, item, it = heapq.heappop(heap)
                yield item
                nxt = next(it, None)
                if nxt is not None:
                    heapq.heappush(heap, (nxt[0], index, nxt, it))
        """,
        why="""The heap holds at most one pending item per stream, so memory depends on the number of servers, not on the length of the
        logs, and infinite streams work. Each step pops the earliest item in O(log s) for `s` streams and replaces it with the next
        item from the same stream. The tuple order does the work: the timestamp sorts, the stream index breaks ties in the order the
        streams were passed, and because indices are unique, Python never has to compare the item or iterator (which could fail or
        be meaningless). `heapq.merge(*streams, key=...)` is the library version of exactly this. It is also the merge step of
        external merge sort, which sorts files larger than memory by sorting chunks and merging them."""),
    predict("Lazy tools and their edges", "hard",
        code="""
        from itertools import groupby, tee, takewhile, zip_longest, product, chain

        it = iter([1, 2, 3, 4])
        print(list(zip(it, it)))
        a, b = tee([1, 2, 3])
        print(next(a), next(a), list(b))
        print(list(takewhile(str.isdigit, ["1", "22", "x", "3"])), len(list(product("ab", repeat=3))))
        keys = [k for k, _ in groupby(sorted("banana"))]
        print(keys, list(chain.from_iterable(["ab", "cd"])))
        print(list(zip_longest([1, 2, 3], "ab")))
        """,
        hints=["`zip(it, it)` pulls from the **same** iterator twice per pair.", "`tee` copies are independent; `b` still starts at the beginning."],
        why="""`zip(it, it)` takes one item for the first slot and the next for the second, from the same iterator, so it pairs
        neighbours without overlap: a well-known idiom for grouping a flat stream into pairs. The `tee` copy `b` is independent of
        `a`, so it still yields everything (buffered while `a` ran ahead). `takewhile` stops at `"x"` for good, so `"3"` is never
        reached. `product` with `repeat=3` over two items gives 2 ** 3 = 8 tuples. Sorting `banana` makes equal letters adjacent, so
        `groupby` returns each distinct letter once. `zip_longest` fills the missing third partner with `None`."""),
)

section("interview", "Interview questions",
    explain("How is `itertools.groupby` different from SQL's GROUP BY, and how do you use it correctly?", "medium", tag="Interview",
        why="""SQL's `GROUP BY` collects every row with the same key from anywhere in the table. `groupby` only groups **consecutive**
        items with the same key, so on unsorted data a key can appear in several separate groups. To group like SQL, sort by the
        same key function first, then group. Each group is an iterator that shares the underlying stream, so it must be consumed
        (or copied with `list`) before moving to the next key; collecting `list(groupby(...))` first leaves every group empty. The
        consecutive behaviour is also a feature: run-length encoding, or splitting an already-ordered stream into blocks, works
        without sorting and stays lazy. For simple aggregation of unsorted data, one pass with a `defaultdict` or `Counter` is
        usually simpler and avoids the O(n log n) sort."""),
    explain("Which operations break laziness in a pipeline, and how do you design around them?", "medium", tag="Interview",
        why="""Anything that needs all the data before it can answer: `sorted`, `reversed` (needs a sequence), `len`, building a `list` or
        `set`, `sorted` followed by `groupby`, and full aggregates such as `max`, `min` and `sum`, which read everything (though in
        constant memory). Also any step that iterates its input twice, and `tee` when one copy runs far ahead of another (its
        buffer grows). Design around them by putting such steps at the end, bounding what they hold (a heap for top-k, a running
        aggregate instead of a list, a dedupe set of hashes rather than full texts), relying on input that is already sorted (then
        `groupby` streams), merging sorted streams with `heapq.merge` instead of sorting their union, and processing in fixed-size
        batches. When the data truly needs a global sort larger than memory, use external sorting or a tool built for it (a
        database, DuckDB, Spark)."""),
    explain("Design a pipeline that embeds 100 million documents. What would you build, and what can go wrong?", "hard", tag="Interview",
        why="""A streaming pipeline: read documents lazily (files or a database cursor), parse and validate each record, normalise and
        chunk the text, deduplicate with hashes of the normalised chunks, batch to the embedding API's limits (texts and tokens per
        request), call the API with several requests in flight (async or a thread pool, within the rate limit), and write vectors
        to the store in batches. What goes wrong at this scale: transient API errors and rate limits (retries with exponential
        backoff and jitter); crashes halfway through, so make it **resumable**, by recording processed ids or offsets as
        checkpoints, and **idempotent**, by using deterministic chunk ids so re-running upserts instead of duplicating; bad records
        (skip and log them instead of failing the job); memory growth from unbounded buffers or a dedupe set (store hashes, or use a
        key-value store); cost (estimate tokens up front and deduplicate before embedding); and consistency (record the model name and
        version with every vector, since vectors from different embedding models cannot be mixed). Measure throughput and error
        rates as it runs, and test the whole pipeline on a small sample first."""),
)

recap(
    "Chain generators into pipelines: nothing runs until the end is consumed, then items flow through one at a time in constant memory.",
    "`islice` slices streams; `takewhile`/`dropwhile` act on a prefix; `chain`, `zip_longest`, `pairwise`, `batched` and `accumulate` reshape streams lazily.",
    "`groupby` groups **consecutive** items: sort by the same key first, and consume each group before moving on.",
    "`product`, `combinations` and `permutations` grow fast; `product` is grid search, `combinations` all pairs.",
    "`sorted`, `len`, `list` and far-ahead `tee` copies break laziness. Merge sorted streams with a heap instead of sorting.",
)
