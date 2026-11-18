from lesson import *

lesson(
    id="m6-p", num="6.P", title="Module 6 practice set and mini project",
    intro="Mixed problems from all of Module 6: list, dict and set comprehensions, generators, and lazy pipelines with "
          "`itertools`. Then a mini project that needs all of it: a streaming evaluation harness for an LLM classifier.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project evaluation harness llm classifier comprehension generator pipeline itertools batched groupby confusion matrix kfold stratified sample stop sequence",
)

section("how", "How to use this page",
    p("""For each problem, decide first whether the result must be **stored** or only **streamed**. If you need the result more than
    once, need its length, need to index it, or will return it to a caller who expects a list, build it: a list, dict or set
    comprehension (6.1, 6.2). If it is consumed once, may be large, or may be stopped early, stream it: a generator function or
    expression (6.3), chained with `itertools` (6.4). Then check the traps of each choice: a comprehension that repeats a key
    or shares a mutable value, a generator that is consumed twice or validates too late."""),
    p("""The problems are mixed on purpose, from easy to hard. The mini project at the end combines every lesson in one realistic
    program."""),
)

section("set", "Practice set",
    predict("Brackets decide everything", "easy",
        code="""
        xs = [3, 1, 4, 1, 5]
        a = [x * 2 for x in xs if x > 1]
        b = {x * 2 for x in xs if x > 1}
        c = {x: x * 2 for x in xs if x > 1}
        d = (x * 2 for x in xs if x > 1)
        print(a, sorted(b), c)
        print(type(d).__name__, sum(d), sum(d))
        """,
        hints=["Square brackets: list. Braces with one expression: set; with `key: value`: dict. Parentheses: a generator, used once."],
        why="""The same loop and filter give four different results depending only on the brackets. The filter removed the only repeated
        value (the two 1s), so the list and the sorted set print the same here; with repeats, the list would keep them and the set
        would not. The dict maps each kept `x` to its double, and the generator computes nothing until `sum` asks; the second `sum`
        finds it exhausted and returns 0."""),
    write("Number every turn of every conversation", "easy", tag="GenAI",
        prompt="""Write `turn_index(conversations)` where `conversations` maps conversation id to a list of messages (dicts with
        `"role"`). Return a list of `(conversation_id, turn_number, role)` tuples, turns numbered from 1 within each conversation,
        conversations in sorted id order, using one comprehension.""",
        code="""
        def turn_index(conversations):
            pass
        """,
        tests="""
        convs = {"c2": [{"role": "user"}, {"role": "assistant"}], "c1": [{"role": "user"}], "c3": []}
        assert turn_index(convs) == [("c1", 1, "user"), ("c2", 1, "user"), ("c2", 2, "assistant")]
        assert turn_index({}) == []
        """,
        hints=["Two `for` clauses: the outer over `sorted(conversations.items())`, the inner over `enumerate(messages, start=1)`."],
        solution="""
        def turn_index(conversations):
            return [
                (cid, n, msg["role"])
                for cid, messages in sorted(conversations.items())
                for n, msg in enumerate(messages, start=1)
            ]
        """,
        why="""The outer `for` walks conversations in sorted order, and the inner one numbers the messages of each; the inner `enumerate`
        restarts at 1 for every conversation because it is created anew for each outer item. An empty conversation contributes
        nothing. This flat index is the shape you load into a DataFrame to analyse conversation lengths or role patterns."""),
    fix("A count and a list from one generator", "easy", tag="Data work",
        prompt="""`valid_ids(rows)` should return `(count, ids)` of the rows that have a non-empty `"text"`. The count is right, but
        the list of ids is always empty. Fix it.""",
        code="""
        def valid_ids(rows):
            valid = (r for r in rows if r.get("text", "").strip())
            count = sum(1 for _ in valid)
            return count, [r["id"] for r in valid]
        """,
        tests="""
        rows = [{"id": 1, "text": "a"}, {"id": 2, "text": " "}, {"id": 3}, {"id": 4, "text": "b"}]
        assert valid_ids(rows) == (2, [1, 4])
        assert valid_ids(iter(rows)) == (2, [1, 4])
        assert valid_ids([]) == (0, [])
        """,
        hints=["The generator is exhausted by the count. Build the list once and take its length."],
        solution="""
        def valid_ids(rows):
            ids = [r["id"] for r in rows if r.get("text", "").strip()]
            return len(ids), ids
        """,
        why="""Counting consumed the generator, so the comprehension that followed got nothing (6.3). When you need a result twice,
        store it once: the list gives both the ids and, through `len`, the count, in one pass over `rows`, which also makes it work
        when `rows` itself is an iterator, as in the second test."""),
    predict("Keys, runs and slices", "medium",
        code="""
        from itertools import groupby, islice, accumulate

        words = ["Refund", "refund", "EU", "eu", "Policy"]
        print({w.lower(): i for i, w in enumerate(words)})
        print([(k, len(list(g))) for k, g in groupby(words, key=str.lower)])
        print(list(islice(accumulate(len(w) for w in words), 1, 4)))
        print(next((w for w in words if w.isupper()), None), next((w for w in words if w.isdigit()), "none"))
        """,
        hints=["Repeated dict keys keep the last value. `groupby` groups consecutive items with the same key."],
        why="""Lower-casing makes pairs of words collide: each key keeps the index of its **last** occurrence. `groupby` with
        `str.lower` as the key sees three runs, because the equal words happen to be adjacent. `accumulate` gives running totals of
        the lengths (6, 12, 14, 16, 22), and `islice(..., 1, 4)` takes positions 1 to 3. `next` with a default finds the first match
        or returns the default; `"EU"` is the first all-capital word."""),
    write("K-fold split indices", "medium", tag="ML",
        prompt="""Write a generator `kfold(n, k)` yielding `(train, val)` pairs of index lists for k-fold cross-validation without
        shuffling, like scikit-learn's `KFold`: the indices `0..n-1` are cut into `k` consecutive folds, the first `n % k` folds one
        item larger than the rest; each fold is the validation set once, and the other indices, in order, are the training set.
        Raise `ValueError` at the call if `k < 2` or `k > n`.""",
        code="""
        def kfold(n, k):
            pass
        """,
        tests="""
        folds = list(kfold(7, 3))
        assert [v for _, v in folds] == [[0, 1, 2], [3, 4], [5, 6]]
        assert folds[1][0] == [0, 1, 2, 5, 6]
        assert all(sorted(t + v) == list(range(7)) for t, v in folds)
        assert [len(v) for _, v in kfold(10, 5)] == [2] * 5
        for bad in [(5, 1), (3, 4)]:
            try:
                kfold(*bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["Fold sizes: `[n // k + (1 if i < n % k else 0) for i in range(k)]`. Walk them with a running start.",
               "Validate in a normal function and return an inner generator, so bad arguments fail at the call (6.3)."],
        solution="""
        def kfold(n, k):
            if not 2 <= k <= n:
                raise ValueError("need 2 <= k <= n")
            return _folds(n, k)


        def _folds(n, k):
            sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
            start = 0
            for size in sizes:
                val = list(range(start, start + size))
                train = [i for i in range(n) if not start <= i < start + size]
                yield train, val
                start += size
        """,
        why="""The fold sizes come from integer division with the remainder spread over the first folds, so sizes differ by at most one
        and add up to `n`. Each validation fold is a `range` slice of consecutive indices, and the training set is every other
        index, kept in order by a filtered comprehension. Yielding folds one at a time lets a training loop start the first fold
        immediately. The wrapper makes invalid `k` fail at the call, not at the first `next`. Real cross-validation usually
        shuffles first (with a fixed seed) or stratifies by label, so that each fold has a similar class mix."""),
    choose("Filtering stop words: list or set", "medium", tag="ML",
        prompt="Both remove 300 stop words from 200,000 tokens. Which is faster?",
        setup="""stop_list = [f"w{i}" for i in range(300)]
tokens = [f"w{i % 600}" for i in range(200_000)]""",
        options={
            "a": "kept = [t for t in tokens if t not in stop_list]",
            "b": "stop_set = set(stop_list)\nkept = [t for t in tokens if t not in stop_set]",
        },
        answer="b",
        hints=["What does `not in` cost for a list, and for a set?"],
        why="""`not in` on a list scans it, up to 300 comparisons per token, and every kept token (half of them here) pays for the
        full scan. A set lookup is one hash and usually one comparison (4.4). The comprehension is the same in both; the data
        structure in its filter decides the speed. Build the set once, outside the comprehension: `if t not in set(stop_list)`
        would rebuild it for every token."""),
    write("Top k per group", "medium", tag="RAG",
        prompt="""Write `top_per_source(results, k)` returning a dict from source to the texts of its `k` highest-scoring results,
        best first, with sources in sorted order. Results are dicts with `"source"`, `"text"` and `"score"`, in any order. Use one
        pass to group and `heapq.nlargest` per group.""",
        code="""
        import heapq
        from collections import defaultdict

        def top_per_source(results, k):
            pass
        """,
        tests="""
        results = [{"source": "faq", "text": "a", "score": 0.5}, {"source": "terms", "text": "b", "score": 0.9},
                   {"source": "faq", "text": "c", "score": 0.8}, {"source": "faq", "text": "d", "score": 0.7},
                   {"source": "terms", "text": "e", "score": 0.1}]
        assert top_per_source(results, 2) == {"faq": ["c", "d"], "terms": ["b", "e"]}
        assert list(top_per_source(results, 1)) == ["faq", "terms"]
        assert top_per_source([], 3) == {}
        """,
        hints=["Group with a `defaultdict(list)`, then a dict comprehension over `sorted(groups.items())` with `heapq.nlargest(k, items, key=...)`."],
        solution="""
        import heapq
        from collections import defaultdict

        def top_per_source(results, k):
            groups = defaultdict(list)
            for r in results:
                groups[r["source"]].append(r)
            return {
                source: [r["text"] for r in heapq.nlargest(k, items, key=lambda r: r["score"])]
                for source, items in sorted(groups.items())
            }
        """,
        why="""Grouping is accumulation, so it is a loop with a `defaultdict` (6.2); the comprehension then turns each group into its
        summary. `heapq.nlargest` returns the `k` best in descending order without sorting the whole group, which matters when
        groups are large and `k` is small (4.2). Sorting the items of `groups` fixes the source order. Limiting results per
        source is a common RAG step, to stop one long document from filling the whole context."""),
    trace("A stateful pipeline step by step", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        from itertools import islice

        def dedupe(xs):
            seen = set()
            for x in xs:
                if x not in seen:
                    seen.add(x)
                    yield x

        def running(xs):
            total = 0
            for x in xs:
                total += x
                yield total

        data = [3, 1, 3, 2, 1, 5]
        r = list(dedupe(data))  # row: "dedupe"
        r = list(running(dedupe(data)))  # row: "running totals of unique"
        r = list(islice(running(data), 2, 4))  # row: "slice of running"
        g = running(dedupe(data))
        r = [next(g), next(g)]  # row: "two values"
        r = sum(g)  # row: "the rest"
        """,
        trace_vars=["r"],
        hints=["`dedupe` keeps the first occurrence of each value. The generator `g` continues where it stopped."],
        why="""`dedupe` keeps 3, 1, 2, 5 in first-seen order. Running totals over those are 3, 4, 6, 11. On the raw data, the running
        totals are 3, 4, 7, 9, 10, 15, and positions 2 and 3 are 7 and 9. `g` yields 3 and 4 first; `sum(g)` then adds only what
        is left of the same generator, 6 + 11."""),
    refactor("Loops to a lazy pipeline", "medium", tag="Data work",
        prompt="Rewrite as a pipeline of generator expressions and `itertools.islice`, same result. Keep the tests green.",
        code="""
        def first_queries(lines, n):
            out = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                query = line.split("\\t")[-1].lower()
                if len(query) < 3:
                    continue
                out.append(query)
                if len(out) == n:
                    break
            return out
        """,
        tests="""
        lines = ["# ts\\tquery", "1\\tRefund", "", "2\\tok", "3\\tReset Password", "4\\tInvoice", "5\\tLate fee"]
        assert first_queries(lines, 2) == ["refund", "reset password"]
        assert first_queries(lines, 10) == ["refund", "reset password", "invoice", "late fee"]
        assert first_queries([], 3) == []
        """,
        hints=["Steps: strip, drop blank and comment lines, take the last tab field lower-cased, drop short ones, take `n` with `islice`."],
        solution="""
        from itertools import islice

        def first_queries(lines, n):
            stripped = (line.strip() for line in lines)
            content = (line for line in stripped if line and not line.startswith("#"))
            queries = (line.split("\\t")[-1].lower() for line in content)
            long_enough = (q for q in queries if len(q) >= 3)
            return list(islice(long_enough, n))
        """,
        why="""Each line of the pipeline does one job and has a name that says what it holds, which replaces the `continue` and `break`
        bookkeeping. Nothing runs until `islice` pulls, and it stops after `n` results, so the early exit of the original loop is
        kept: the pipeline never reads past the `n`th query. Each step can now be reused or tested on its own. For a very short
        function, the original loop is also fine; the pipeline style pays off as steps grow."""),
    write("Stop sequences across streamed pieces", "hard", tag="GenAI",
        prompt="""When a model ignores the API's stop parameter, you apply the stop sequence yourself while streaming. Write a
        generator `until_stop(deltas, stop)` that yields text from the stream, never yielding any part of `stop` or anything after it,
        even when `stop` is split across pieces. Hold back only as much text as could be the start of `stop`; yield everything else
        as early as possible. If the stream ends without the stop, yield what was held back.""",
        code="""
        def until_stop(deltas, stop):
            pass
        """,
        tests="""
        assert "".join(until_stop(["Answer: 4", "2\\nObs", "ervation: x"], "\\nObservation:")) == "Answer: 42"
        assert "".join(until_stop(["abc", "def"], "XYZ")) == "abcdef"
        assert "".join(until_stop(["say STO", "P now", "STOP"], "STOP")) == "say "
        assert "".join(until_stop(["abcST", "x"], "STOP")) == "abcSTx"
        g = until_stop(["Hello wor", "ld, more"], "\\n\\nUser:")
        assert next(g) == "Hello wor"
        assert list(until_stop([], "X")) == []
        """,
        hints=["Keep a `buffer`. After adding each piece, if `stop` is in the buffer, yield the part before it and `return`.",
               "Otherwise, find the longest suffix of the buffer that is a prefix of `stop`; yield everything before that suffix and keep the suffix."],
        solution="""
        def until_stop(deltas, stop):
            buffer = ""
            for delta in deltas:
                buffer += delta
                cut = buffer.find(stop)
                if cut != -1:
                    if cut:
                        yield buffer[:cut]
                    return
                keep = 0
                for size in range(min(len(stop) - 1, len(buffer)), 0, -1):
                    if stop.startswith(buffer[-size:]):
                        keep = size
                        break
                safe = buffer[:len(buffer) - keep]
                if safe:
                    yield safe
                buffer = buffer[len(buffer) - keep:]
            if buffer:
                yield buffer
        """,
        why="""Checking each piece alone misses a stop that is split across pieces, like `"\\nObs"` + `"ervation:"`. Buffering everything
        would work but defeats streaming. The middle ground is to hold back only a suffix that could still grow into the stop: the
        longest end of the buffer that is a start of `stop`, at most `len(stop) - 1` characters. Everything before it can never
        become part of a stop, so it is yielded at once, which the `next(g)` test checks. When the held text turns out not to be the
        stop (`"ST"` followed by `"x"`), it is released with the next piece. Agent frameworks do exactly this, both for custom stop
        sequences and to hide markers such as `"Observation:"` from users."""),
    fix("Read the code: a stratified sample", "hard", tag="ML",
        prompt="""This draws up to `per_label` random examples of each label for a balanced evaluation set, reproducibly with a seed,
        and returns them with labels in sorted order. With a generator as input it returns nothing; with a list, every label gets
        examples of other labels; and the label order is not sorted. Read it, find the bugs and fix them.""",
        code="""
        import random


        def stratified_sample(records, per_label, seed):
            rng = random.Random(seed)
            buckets = dict.fromkeys({r["label"] for r in records}, [])
            for r in records:
                buckets[r["label"]].append(r)
            return {
                label: rng.sample(items, min(per_label, len(items)))
                for label, items in buckets.items()
            }
        """,
        tests="""
        records = [{"id": i, "label": ["spam", "ham", "phish"][i % 3]} for i in range(20)] + [{"id": 99, "label": "ham"}]
        out = stratified_sample(iter(records), 3, seed=1)
        assert list(out) == ["ham", "phish", "spam"]
        assert all(len(v) == 3 and all(r["label"] == label for r in v) for label, v in out.items())
        assert stratified_sample(records, 3, seed=1) == stratified_sample(records, 3, seed=1)
        small = stratified_sample([{"id": 1, "label": "a"}, {"id": 2, "label": "b"}, {"id": 3, "label": "b"}], 5, seed=0)
        assert [len(v) for v in small.values()] == [1, 2]
        assert stratified_sample([], 2, seed=0) == {}
        """,
        hints=["The set comprehension walks `records` once; if it is a generator, the loop afterwards gets nothing. Group in one pass.",
               "`dict.fromkeys(..., [])` shares one list (6.2). And the dict built from a set of strings follows the set's order."],
        solution="""
        import random
        from collections import defaultdict


        def stratified_sample(records, per_label, seed):
            rng = random.Random(seed)
            buckets = defaultdict(list)
            for r in records:
                buckets[r["label"]].append(r)
            return {
                label: rng.sample(items, min(per_label, len(items)))
                for label, items in sorted(buckets.items())
            }
        """,
        why="""Three bugs from this module. The set comprehension that collected labels consumed a generator input, so the grouping loop
        saw nothing (6.3); grouping in a single pass with a `defaultdict` needs only one walk. `dict.fromkeys(labels, [])` gave
        every label the same list, so each "bucket" held every record (6.2). And iterating a dict built from a set of strings
        follows hash order, which varies between processes; besides breaking the required sorted order, it made the sample itself
        irreproducible, because the shared random generator is consumed label by label, so a different label order gives different
        samples for the same seed. Sorting the labels fixes both. `min(per_label, len(items))` keeps `rng.sample` from failing on
        rare labels."""),
    predict("Everything at once", "hard",
        code="""
        from itertools import batched, chain, groupby

        def gen():
            for i in range(1, 8):
                yield i

        g = gen()
        evens = [x for x in g if x % 2 == 0]
        print(evens, list(g))
        pairs = {k: list(v) for k, v in groupby(sorted(range(10), key=lambda n: n % 3), key=lambda n: n % 3)}
        print(pairs)
        print([sum(b) for b in batched(chain(range(3), [10, 20]), 2)])
        fs = {name: (lambda x, n=n: x * n) for name, n in [("double", 2), ("triple", 3)]}
        print({k: f(5) for k, f in fs.items()})
        """,
        hints=["The comprehension consumes `g` completely.", "`sorted` with a key is stable, so numbers keep their order inside each remainder group."],
        why="""The list comprehension runs the generator to the end, so `list(g)` afterwards is empty. Sorting by `n % 3` puts all
        remainder-0 numbers first, keeping their original order (stable sort, 4.2), so `groupby` sees exactly three runs and the dict
        comprehension stores each group as a list before moving on. `chain` joins the two sources and `batched` cuts the joined
        stream into pairs: (0, 1), (2, 10), (20,). The lambdas bind `n` as a default argument, so each keeps its own factor (6.1)."""),
    explain("How would you process a 20 GB CSV file in Python on a machine with 8 GB of RAM?", "medium", tag="Interview",
        why="""Stream it instead of loading it. With the standard library, open the file with an explicit encoding and pass it to
        `csv.reader` or `csv.DictReader`, which yields one row at a time; build the processing as a pipeline of generators (parse,
        validate, transform, filter) and aggregate incrementally with `Counter`, `defaultdict` or running totals, so memory depends
        on the size of the aggregates, not the file. If the output must be written, write as you go. With pandas, use
        `read_csv(..., chunksize=100_000)` (or `usecols` and `dtype` to shrink each chunk) and combine per-chunk results. For
        heavier analytics, tools like Polars (lazy `scan_csv` with a streaming engine) or DuckDB query the file directly without
        loading it, and converting it once to Parquet makes later reads much faster. Watch for steps that need all the data at
        once (sorting, exact distinct counts, joins); they need external sorting, approximate algorithms or a database."""),
    explain("What are the trade-offs between eager and lazy evaluation in a data pipeline?", "hard", tag="Interview",
        why="""Eager code (lists, comprehensions, DataFrames) computes everything at each step: it is simple to inspect and debug, results
        can be reused, indexed and counted, and errors appear at the step that caused them, but memory grows with the data and
        nothing is available until the whole step is done. Lazy code (generators, iterators, lazy query engines) computes items only
        when asked: memory stays constant, the first results arrive immediately, early exits skip work, and infinite or streaming
        sources work, but results are one-shot, have no length, and errors surface where the data is consumed, possibly far from
        the code that caused them; debugging needs care because inspecting a generator consumes it. Laziness also lets an engine
        optimise the whole plan (Polars, Spark, SQL databases push filters down and skip columns). A practical pattern is lazy
        streaming for the large, linear part of a pipeline, and eager materialisation for small results that are reused, with
        validation at the boundaries so errors are caught close to their source."""),
)

section("project", "Mini project: a streaming evaluation harness",
    p("""You are evaluating an LLM as a text classifier on a labelled test set stored as JSON Lines. The model is called in batches
    and replies with free text such as `"Label: spam"`. Build the harness. It must stream the file, batch the model calls, parse
    replies, and report metrics. Every rule in the spec maps to a lesson in this module, and the tests check each one."""),
    write("Evaluate a classifier on a stream", "hard", key="eval-harness", tag="Project",
        prompt="""Implement `evaluate(lines, predict, labels, batch_size)`. `lines` is an iterable of JSON lines with `"id"`,
        `"text"` and `"label"`; `predict(texts)` returns one reply string per text; `labels` is the list of valid labels. Return a
        `Report` named tuple:

        - **`invalid`**: line numbers (from 1) of lines that are not valid JSON, lack one of the three fields, or have a label not
          in `labels`. Blank lines are skipped silently. Invalid lines are not evaluated.
        - **`calls`**: how many times `predict` was called. Valid records are sent in batches of `batch_size`, in file order.
        - **`unparsed`**: ids of records whose reply could not be parsed, in file order. A reply is parsed by taking the text after
          its last `:` (or the whole reply if there is none), stripped and case-folded; it must then equal a label (compared
          case-folded). Unparsed records count as wrong.
        - **`accuracy`**: correct predictions divided by the number of valid records, rounded to 4 decimals (0.0 if none).
        - **`confusion`**: `{gold: {predicted: count}}` for parsed predictions, with every label from `labels` (sorted) in both
          levels.
        - **`per_label`**: `{label: {"precision": ..., "recall": ..., "support": ...}}` for every label, sorted. Support is the
          number of valid records with that gold label; recall is correct ones over support; precision is correct ones over
          parsed predictions of that label. Round to 3 decimals; 0.0 when dividing by zero.

        It must be lazy: if the caller only needs the first batch evaluated, the harness must not read the whole file before
        calling `predict` (the tests check the order of reads and calls).""",
        code="""
        import json
        from itertools import batched
        from typing import NamedTuple


        class Report(NamedTuple):
            accuracy: float
            per_label: dict
            confusion: dict
            invalid: list
            unparsed: list
            calls: int


        def evaluate(lines, predict, labels, batch_size):
            pass
        """,
        tests="""
        lines = [
            '{"id": "a", "text": "Win a prize now", "label": "spam"}',
            '{"id": "b", "text": "Lunch at noon?", "label": "ham"}',
            '',
            '{"id": "c", "text": "Verify your account", "label": "phish"}',
            '{not json',
            '{"id": "d", "text": "Cheap pills", "label": "spam"}',
            '{"id": "e", "text": "Meeting notes", "label": "HAM"}',
            '{"id": "f", "text": "Reset password here", "label": "phish"}',
            '{"id": "g", "text": "no label"}',
            '{"id": "h", "text": "Your invoice", "label": "ham"}',
        ]
        replies = {"a": "Label: spam", "b": "label: Ham", "c": "spam", "d": "I think this is spam: SPAM",
                   "e": "Label: ham", "f": "Label: phishing", "h": "Label: ham"}
        log = []
        def predict(texts):
            log.append(("predict", len(texts)))
            by_text = {"Win a prize now": "a", "Lunch at noon?": "b", "Verify your account": "c", "Cheap pills": "d",
                       "Meeting notes": "e", "Reset password here": "f", "Your invoice": "h"}
            return [replies[by_text[t]] for t in texts]

        r = evaluate(lines, predict, ["spam", "ham", "phish"], batch_size=4)
        assert r.invalid == [5, 9]
        assert r.calls == 2 and log == [("predict", 4), ("predict", 3)]
        assert r.unparsed == ["f"]
        assert r.accuracy == 0.7143
        assert r.confusion == {"ham": {"ham": 3, "phish": 0, "spam": 0}, "phish": {"ham": 0, "phish": 0, "spam": 1},
                               "spam": {"ham": 0, "phish": 0, "spam": 2}}
        assert list(r.per_label) == ["ham", "phish", "spam"]
        assert r.per_label["spam"] == {"precision": 0.667, "recall": 1.0, "support": 2}
        assert r.per_label["phish"] == {"precision": 0.0, "recall": 0.0, "support": 2}
        assert r.per_label["ham"] == {"precision": 1.0, "recall": 1.0, "support": 3}

        log.clear()
        def reading(ls):
            for i, line in enumerate(ls, 1):
                log.append(("read", i))
                yield line
        evaluate(reading(lines), predict, ["spam", "ham", "phish"], batch_size=2)
        assert log.index(("predict", 2)) < log.index(("read", 4))

        empty = evaluate([], predict, ["x"], 3)
        assert empty == Report(0.0, {"x": {"precision": 0.0, "recall": 0.0, "support": 0}}, {"x": {"x": 0}}, [], [], 0)
        """,
        hints=["A generator `_records(lines, valid, invalid)` with `enumerate(lines, start=1)` parses each line, appends bad line numbers to `invalid` and yields good records (6.3).",
               "`for batch in batched(records, batch_size)`: call `predict` once, then `zip` the batch with the replies and parse each reply (6.4).",
               "Collect `(gold, predicted_or_None)` pairs in a list, then build the confusion matrix and metrics with nested dict comprehensions over `sorted(labels)` and a `Counter` of pairs (6.2).",
               "Labels in the file may differ in case (`\"HAM\"`): compare with `casefold()` and map back to the canonical label with a dict comprehension."],
        solution="""
        import json
        from collections import Counter
        from itertools import batched
        from typing import NamedTuple


        class Report(NamedTuple):
            accuracy: float
            per_label: dict
            confusion: dict
            invalid: list
            unparsed: list
            calls: int


        def _ratio(num, den):
            return round(num / den, 3) if den else 0.0


        def _records(lines, canonical, invalid):
            for lineno, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    gold = canonical.get(str(rec["label"]).casefold())
                    rid, text = rec["id"], rec["text"]
                except (json.JSONDecodeError, KeyError, TypeError):
                    invalid.append(lineno)
                    continue
                if gold is None:
                    invalid.append(lineno)
                    continue
                yield rid, text, gold


        def _parse(reply, canonical):
            return canonical.get(reply.rsplit(":", 1)[-1].strip().casefold())


        def evaluate(lines, predict, labels, batch_size):
            canonical = {label.casefold(): label for label in labels}
            classes = sorted(labels)
            invalid, unparsed, pairs = [], [], []
            calls = 0
            for batch in batched(_records(lines, canonical, invalid), batch_size):
                replies = predict([text for _, text, _ in batch])
                calls += 1
                for (rid, _, gold), reply in zip(batch, replies, strict=True):
                    pred = _parse(reply, canonical)
                    if pred is None:
                        unparsed.append(rid)
                    pairs.append((gold, pred))

            counts = Counter(p for p in pairs if p[1] is not None)
            confusion = {g: {p: counts[(g, p)] for p in classes} for g in classes}
            correct = sum(confusion[c][c] for c in classes)
            support = Counter(g for g, _ in pairs)
            predicted = Counter(p for _, p in pairs if p is not None)
            per_label = {
                c: {"precision": _ratio(confusion[c][c], predicted[c]),
                    "recall": _ratio(confusion[c][c], support[c]),
                    "support": support[c]}
                for c in classes
            }
            accuracy = round(correct / len(pairs), 4) if pairs else 0.0
            return Report(accuracy, per_label, confusion, invalid, unparsed, calls)
        """,
        why="""Every lesson of the module has a job here:

        - **Generators (6.3):** `_records` streams the file, numbering lines with `enumerate(..., start=1)`, skipping blank lines,
          and reporting bad ones through the `invalid` list instead of stopping the run. Nothing is read until the batches ask for
          records.
        - **Lazy pipelines (6.4):** `batched` pulls exactly `batch_size` records before each `predict` call, which is why the first
          call happens after reading only the first few lines, as the read-order test checks. `zip(..., strict=True)` fails loudly if
          the model returns the wrong number of replies.
        - **Dict comprehensions (6.2):** `canonical` maps case-folded labels back to their official spelling, which handles `"HAM"`
          in the data and `"label: Ham"` in a reply; the confusion matrix and per-label metrics are nested comprehensions over the
          sorted labels, so every label appears in a fixed order, including ones with no examples.
        - **List comprehensions and generator expressions (6.1):** the texts of each batch, and the filtered pairs fed into each
          `Counter`.

        Unparsed replies (`"Label: phishing"` is not a valid label) count against accuracy but are left out of the confusion matrix
        and of precision, which is the usual convention, and they are reported by id so you can look at them: they often reveal a
        prompt that needs a clearer label list. The pairs list grows with the dataset, but it holds two short strings per record; for
        a really large evaluation, the `Counter`s could be updated inside the loop instead. This is the core of tools like OpenAI's
        evals, Promptfoo or a scikit-learn `classification_report` run on LLM output."""),
)

recap(
    "Store or stream: build lists, dicts and sets when results are reused or small; use generators and `itertools` when consumed once, large or stopped early.",
    "Comprehensions transform and filter; grouping and counting accumulate (`defaultdict`, `Counter`), then comprehensions summarise.",
    "Watch the collisions: repeated dict keys keep the last value, `fromkeys` shares one mutable value, sets of strings have no stable order.",
    "Generators are one-shot and run late: consume once, validate in a wrapper, keep resources open inside the generator.",
    "Pipelines of small lazy steps (`islice`, `batched`, `accumulate`, `groupby` on sorted data) keep memory flat and results early.",
)
