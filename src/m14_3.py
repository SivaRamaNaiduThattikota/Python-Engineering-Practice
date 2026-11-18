from lesson import *

lesson(
    id="m14-3", num="14.3", title="Processes",
    intro="For CPU-bound Python code, the way past the GIL is several processes, each with its own interpreter on its own core. "
          "`ProcessPoolExecutor` and `multiprocessing`, what must be picklable, the `__main__` guard and start methods, task size "
          "and chunking, loading a model once per worker with an initializer, sending paths instead of data, and when to vectorise "
          "instead. On this site the process pool runs tasks inline but checks picklability the way real processes do.",
    desc="`multiprocessing` and `ProcessPoolExecutor` for CPU-bound work.",
    keys="multiprocessing processpoolexecutor process pool pickle picklingerror lambda top-level function partial __main__ guard spawn fork forkserver start method chunksize chunking initializer initargs shared memory vectorise numpy cpu-bound overhead",
)

term("Process", "A running program with its own memory and its own Python interpreter. Several processes can run Python code on several cores at once.")
term("Pickling", "Turning a Python object into bytes (with `pickle`) so it can be sent to another process; functions and classes are sent by name.")
term("Start method", "How `multiprocessing` creates a worker process: `spawn` (a fresh interpreter), `fork` (a copy of the parent) or `forkserver`.")

section("pool", "`ProcessPoolExecutor`",
    p("""`concurrent.futures.ProcessPoolExecutor(max_workers=n)` has the same interface as the thread pool of 14.2 (`submit`, `map`, `as_completed`, futures), but each
    worker is a separate **process**. Each has its own interpreter and its own GIL, so pure-Python computation runs truly in parallel, one task per core. The
    default `max_workers` is the number of CPUs, which is the right number for CPU-bound work: more processes than cores just compete for them. The lower-level
    `multiprocessing` module offers `Pool`, `Process`, queues and pipes for the same purpose; for task-based work, the executor is simpler."""),
    p("""The price of separate memory is **communication**. The parent and the workers share nothing, so the function to call, its arguments, and its return value are
    **pickled**, sent through a pipe, and unpickled on the other side. This has three consequences, each covered below: what you send must be picklable, sending
    is not free, and global state in the parent is not visible in the workers unless they create it themselves."""),
)

section("pickle", "What can be sent",
    p("""`pickle` sends **functions and classes by name**: it records "the function `square` in module `tasks`", and the worker imports that module and looks the name up.
    So a worker can receive only functions and classes that are defined at the **top level of an importable module**. Lambdas, functions defined inside other
    functions, and classes defined inside functions have no importable name and fail with `PicklingError`. `functools.partial(top_level_fn, arg)` works, and so
    do bound methods of picklable objects. Arguments and return values must be picklable too: numbers, strings, lists, dicts, dataclasses and NumPy arrays are;
    open files, locks, sockets, generators and database connections are not (`TypeError: cannot pickle ...`)."""),
    ex("""
    import functools, threading
    from concurrent.futures import ProcessPoolExecutor

    def square(x):
        return x * x

    def make_scaler(factor):
        def scale(x):
            return x * factor
        return scale

    candidates = [
        ("top-level function", square, (3,)),
        ("lambda", lambda x: x * x, (3,)),
        ("nested function", make_scaler(2), (3,)),
        ("partial", functools.partial(pow, 2), (10,)),
        ("lock argument", square, (threading.Lock(),)),
    ]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for label, fn, args in candidates:
            error = pool.submit(fn, *args).exception()
            print(f"{label:20} {type(error).__name__ if error else 'ok'}")
    """, "picklable.py"),
    p("""On this site the pool runs tasks in the page, but it pickles the function, arguments and result first, so the same mistakes fail here as on a real machine.
    The failure is stored in the future, like any task error, and appears when you call `result()`."""),
)

section("main", "The `__main__` guard and start methods",
    p("""A worker process must import your code to find the function it will run. With the **`spawn`** start method, the default on Windows and macOS, the worker is a
    fresh interpreter that **imports your main script as a module** (under a name other than `"__main__"`). If the script creates a process pool at top level, each
    worker would try to create its own pool while importing it, and Python stops this with an error. Hence the rule for any script that uses processes: put the
    code that starts work under **`if __name__ == "__main__":`**, so it runs when the file is executed and not when a worker imports it."""),
    p("""On Linux, Python historically used **`fork`**, which copies the parent process, including its memory, so workers started without importing anything; it is
    fast but unsafe when the parent has threads (a lock held by another thread is copied in its locked state). Python 3.14 changed the Linux default to
    **`forkserver`**, which forks workers from a clean server process. Write code that works under `spawn` (top-level functions, the main guard, no reliance on
    inherited globals) and it will work everywhere. `multiprocessing.get_context("spawn")` chooses a method explicitly, and `ProcessPoolExecutor(mp_context=...)`
    passes it to the executor."""),
)

section("size", "Task size, chunking and initializers",
    p("""Every task costs a round trip: pickle the call, send it, unpickle, run, pickle the result, send it back. For a task that takes a microsecond, that overhead
    dominates, and a process pool is **slower** than a plain loop. Make tasks coarse: send **chunks** of items (a list of 1,000 texts per task rather than one), or
    use `executor.map(fn, items, chunksize=1000)`, which batches items for you. The right chunk size balances overhead against load balancing: very large chunks
    leave workers idle at the end while one finishes the last chunk (problem 11)."""),
    p("""Workers often need an expensive resource: a tokenizer, a vocabulary, a spaCy pipeline, a model. Loading it inside every task repeats the work; passing it as an
    argument pickles it every time. Instead, give the executor an **`initializer`**: `ProcessPoolExecutor(initializer=load, initargs=(path,))` runs `load(path)`
    once in each worker when it starts, and `load` stores the resource in a module-level global that the task functions read. Similarly, send **paths, ids or
    offsets, not data**: let each worker open its own file or query its own rows, so only small descriptions cross the process boundary."""),
    p("""Finally, check whether processes are needed at all. Many CPU-bound loops are faster still when **vectorised** with NumPy or pandas, whose inner loops run in C
    (problem 8), and some libraries (tokenizers, BLAS in NumPy, PyTorch) already use several cores internally. Measure with `cProfile` and wall-clock timings
    first, then parallelise what remains."""),
)

section("warmup", "Warm-up",
    predict("Picklable or not", "easy",
        code="""
        import functools
        from concurrent.futures import ProcessPoolExecutor
        from dataclasses import dataclass

        @dataclass
        class Doc:
            id: str
            text: str

        def length(doc):
            return len(doc.text)

        def chunk_lengths(docs):
            return [len(d.text) for d in docs]

        def make_gen(n):
            return (i for i in range(n))

        def make_counter():
            class Counter:
                pass
            return Counter()

        jobs = [
            ("dataclass arg", length, (Doc("a", "refund"),)),
            ("list of docs", chunk_lengths, ([Doc("a", "x"), Doc("b", "yz")],)),
            ("partial", functools.partial(length, Doc("c", "abc")), ()),
            ("lambda", lambda d: d.id, (Doc("d", ""),)),
            ("generator result", make_gen, (3,)),
            ("local class result", make_counter, ()),
        ]
        with ProcessPoolExecutor() as pool:
            for label, fn, args in jobs:
                f = pool.submit(fn, *args)
                print(label, type(f.exception()).__name__ if f.exception() else f.result())
        """,
        hints=["Functions and classes travel by name: they must be top-level. Instances of top-level classes are fine. Results are pickled too."],
        why="""Top-level functions, instances of a top-level dataclass, lists of them and a `partial` of a top-level function are all picklable, so those tasks succeed. A lambda
        has no importable name, so pickling the call fails before it runs. The last two fail on the way **back**: a generator cannot be pickled at all (`TypeError`),
        and an instance of a class defined inside a function cannot be either, because its class has no importable name. Returning plain data from workers avoids
        both."""),
    write("Count tokens in parallel chunks", "easy", tag="GenAI",
        prompt="""Write `chunks(items, size)` returning a list of consecutive slices of `items` of length `size` (the last may be shorter; `size < 1` raises `ValueError`), a
        top-level worker `count_chunk(texts)` returning the word counts of a list of texts, and `parallel_token_counts(texts, workers=4, chunk_size=100)` that sends
        **chunks** to a `ProcessPoolExecutor` and returns one count per text, in the original order.""",
        code="""
        from concurrent.futures import ProcessPoolExecutor

        def chunks(items, size):
            pass

        def count_chunk(texts):
            pass

        def parallel_token_counts(texts, workers=4, chunk_size=100):
            pass
        """,
        tests="""
        assert chunks([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]] and chunks([], 3) == []
        texts = [f"word {'x ' * i}".strip() for i in range(250)]
        counts = parallel_token_counts(texts, workers=3, chunk_size=64)
        assert counts == [len(t.split()) for t in texts] and len(counts) == 250
        assert count_chunk(["a b", "c"]) == [2, 1]
        try:
            chunks([1], 0)
            assert False
        except ValueError:
            pass
        """,
        hints=["`[items[i:i + size] for i in range(0, len(items), size)]`.",
               "`pool.map(count_chunk, chunks(texts, chunk_size))` yields one list per chunk, in order; flatten them."],
        solution="""
        from concurrent.futures import ProcessPoolExecutor


        def chunks(items, size):
            if size < 1:
                raise ValueError("size must be at least 1")
            return [items[i:i + size] for i in range(0, len(items), size)]


        def count_chunk(texts):
            return [len(t.split()) for t in texts]


        def parallel_token_counts(texts, workers=4, chunk_size=100):
            out = []
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for counts in pool.map(count_chunk, chunks(texts, chunk_size)):
                    out.extend(counts)
            return out
        """,
        why="""Each task carries a chunk of texts, so the per-task overhead of pickling and inter-process communication is paid once per chunk instead of once per text, and the
        worker function is top-level, so it can be sent by name. Because `map` returns chunk results in submission order, flattening them restores the text order
        without extra bookkeeping. In production the worker would call a real tokenizer (loaded once per worker with an initializer, problem 5); the structure is the
        same."""),
    fix("A lambda in a process pool", "easy", tag="ML",
        prompt="""`normalise_all` applies a scaling to many feature rows in a process pool, but passes a lambda, so every task fails with `PicklingError`. Fix it with a
        top-level function and `functools.partial` to bind the parameters.""",
        code="""
        from concurrent.futures import ProcessPoolExecutor

        def normalise_all(rows, mean, std, workers=4):
            with ProcessPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(lambda row: [(x - mean) / std for x in row], rows))
        """,
        tests="""
        rows = [[1.0, 3.0], [5.0, 7.0]]
        assert normalise_all(rows, mean=4.0, std=2.0) == [[-1.5, -0.5], [0.5, 1.5]]
        assert normalise_all([], 0.0, 1.0) == []
        """,
        hints=["Define `def scale_row(row, mean, std):` at top level, then `pool.map(functools.partial(scale_row, mean=mean, std=std), rows)`."],
        solution="""
        import functools
        from concurrent.futures import ProcessPoolExecutor

        def scale_row(row, mean, std):
            return [(x - mean) / std for x in row]

        def normalise_all(rows, mean, std, workers=4):
            with ProcessPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(functools.partial(scale_row, mean=mean, std=std), rows))
        """,
        why="""A worker receives the function by name, and a lambda has none, so it cannot be pickled; the same code works with a thread pool, which is why this bug appears when
        someone swaps executors. A top-level function plus `functools.partial` gives a picklable callable with the parameters bound: the partial pickles as "call
        `scale_row` with these keyword arguments". For real feature scaling, NumPy on the whole matrix would be faster than any pool, which is the lesson of
        problem 8."""),
    predict("The cost of small tasks", "easy",
        code="""
        def pool_time(n_items, item_cost, workers, chunk, overhead):
            tasks = -(-n_items // chunk)
            rounds = -(-tasks // workers)
            return rounds * (overhead + chunk * item_cost)

        sequential = 10_000 * 0.00001
        print(round(sequential, 3))
        for chunk in (1, 10, 100, 1000, 2500, 10_000):
            print(chunk, round(pool_time(10_000, 0.00001, workers=4, chunk=chunk, overhead=0.001), 3))
        """,
        hints=["Each task pays the overhead once; tasks are spread over 4 workers in rounds."],
        why="""With one item per task, 10,000 tasks each pay a 1 ms overhead for 10 microseconds of work, so the pool is 25 times slower than a plain loop. Larger chunks amortise
        the overhead until four chunks of 2,500 give one round and the best time, close to a quarter of the sequential time. A single chunk of 10,000 leaves three
        workers idle and is as slow as sequential plus overhead. Real overheads are usually 0.1 to 1 ms per task, so tasks should take at least tens of milliseconds."""),
)

section("medium", "Medium",
    write("Load a vocabulary once per worker", "medium", tag="ML",
        prompt="""Write `init_worker(vocab)` that stores the vocabulary (a list of words) in a module-level global `VOCAB` as a dict word -> index, `featurize(text)` that returns
        a bag-of-words count vector (a list with one count per vocabulary word, other words ignored) using `VOCAB`, and `featurize_all(texts, vocab, workers=2)` that
        creates a `ProcessPoolExecutor` with `initializer=init_worker, initargs=(vocab,)` and maps `featurize` over the texts (with `chunksize=64`).""",
        code="""
        from concurrent.futures import ProcessPoolExecutor

        VOCAB = None

        def init_worker(vocab):
            pass

        def featurize(text):
            pass

        def featurize_all(texts, vocab, workers=2):
            pass
        """,
        tests="""
        vocab = ["refund", "days", "free", "prize"]
        out = featurize_all(["Refund takes 5 days, refund now", "Free prize! FREE", "hello"], vocab)
        assert out == [[2, 1, 0, 0], [0, 0, 2, 1], [0, 0, 0, 0]]
        assert VOCAB == {"refund": 0, "days": 1, "free": 2, "prize": 3}
        init_worker(["a"])
        assert featurize("a a b") == [2]
        """,
        hints=["`global VOCAB` inside `init_worker`. In `featurize`, lower-case, strip punctuation from each word (`w.strip(\".,!?\")`), and count indices.",
               "`pool.map(featurize, texts, chunksize=64)`; with `initializer=init_worker, initargs=(vocab,)` each worker builds `VOCAB` once."],
        solution="""
        from concurrent.futures import ProcessPoolExecutor

        VOCAB = None


        def init_worker(vocab):
            global VOCAB
            VOCAB = {word: i for i, word in enumerate(vocab)}


        def featurize(text):
            vec = [0] * len(VOCAB)
            for word in text.lower().split():
                i = VOCAB.get(word.strip(".,!?"))
                if i is not None:
                    vec[i] += 1
            return vec


        def featurize_all(texts, vocab, workers=2):
            with ProcessPoolExecutor(max_workers=workers, initializer=init_worker, initargs=(vocab,)) as pool:
                return list(pool.map(featurize, texts, chunksize=64))
        """,
        why="""The initializer runs once in each worker process, when it starts, and puts the resource into that process's module globals, where every task reads it; the
        vocabulary crosses the process boundary once per worker instead of once per text. The global is the one exception to "avoid global state" in parallel code,
        because each process has its own copy and nothing is shared. The same pattern loads tokenizers, spaCy pipelines or ONNX models in workers. `chunksize`
        batches the small `featurize` calls to keep per-task overhead low."""),
    predict("__name__ when a module is imported", "medium",
        code="""
        from lessontools import make_module

        print(__name__)
        tasks = make_module("tasks", '''
        print("importing tasks, __name__ =", __name__)

        def square(x):
            return x * x

        if __name__ == "__main__":
            print("starting the pool")
        ''')
        print(tasks.square(7), tasks.__name__)
        """,
        hints=["`make_module(name, source)` imports the source as the module `name`, the way a spawned worker imports your script. Only the file you run is `__main__`."],
        why="""The code you run directly has `__name__ == "__main__"`; a module that is imported gets its own name, so the guarded block does not run on import. That is exactly what
        happens with the `spawn` start method: each worker imports your script as a module, and everything outside the guard runs again in every worker, so any code
        that starts work (creating a pool, training a model, reading a large file) must sit under `if __name__ == "__main__":`."""),
    write("Process files by path", "medium", tag="Data work",
        prompt="""Write a top-level worker `summarise_file(path)` returning `(path, lines, words)` for a UTF-8 text file, and `summarise_files(paths, workers=4)` that sends the
        **paths** (not the contents) to a `ProcessPoolExecutor` and returns `{"files": {path: {"lines": n, "words": m}}, "errors": {path: "ExceptionName"}}`, with files in
        input order.""",
        code="""
        from concurrent.futures import ProcessPoolExecutor

        def summarise_file(path):
            pass

        def summarise_files(paths, workers=4):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        a, b, missing = os.path.join(d, "a.txt"), os.path.join(d, "b.txt"), os.path.join(d, "nope.txt")
        with open(a, "w", encoding="utf-8") as f:
            f.write("Refunds take five days.\\nContact support.\\n")
        with open(b, "w", encoding="utf-8") as f:
            f.write("one\\n\\ntwo three\\n")
        out = summarise_files([a, missing, b], workers=2)
        assert out == {"files": {a: {"lines": 2, "words": 6}, b: {"lines": 3, "words": 3}}, "errors": {missing: "FileNotFoundError"}}
        assert list(out["files"]) == [a, b]
        """,
        hints=["The worker opens the file itself: `with open(path, encoding=\"utf-8\") as f:` and counts lines and words while iterating.",
               "Submit one task per path, keep `(path, future)` pairs in order, and check `future.exception()`."],
        solution="""
        from concurrent.futures import ProcessPoolExecutor


        def summarise_file(path):
            lines = words = 0
            with open(path, encoding="utf-8") as f:
                for line in f:
                    lines += 1
                    words += len(line.split())
            return path, lines, words


        def summarise_files(paths, workers=4):
            files, errors = {}, {}
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [(p, pool.submit(summarise_file, p)) for p in paths]
            for path, future in futures:
                error = future.exception()
                if error is not None:
                    errors[path] = type(error).__name__
                else:
                    _, lines, words = future.result()
                    files[path] = {"lines": lines, "words": words}
            return {"files": files, "errors": errors}
        """,
        why="""Sending a path costs a few dozen bytes; sending the file's contents would pickle and copy every byte from the parent to the worker, which for gigabytes of text
        can take longer than the processing itself and doubles memory use. Each worker opens its own file and streams it (12.1), and only a small summary travels
        back. Errors stay per file: a missing file becomes an entry in `errors`, not a crashed batch. The same principle applies to databases (send ids or ranges,
        let workers query) and to large arrays (use shared memory or memory-mapped files)."""),
    choose("Vectorise before you parallelise", "medium", tag="ML",
        prompt="Both compute the sum of squares of 200,000 floats. Which is faster?",
        setup="""import numpy as np
values = np.random.default_rng(0).random(200_000)
as_list = values.tolist()""",
        options={
            "a": "total = sum(x * x for x in as_list)",
            "b": "total = float(np.dot(values, values))",
        },
        answer="b",
        hints=["Where does each version's loop run: in the Python interpreter, or in compiled code?"],
        why="""The generator expression runs 200,000 iterations in the interpreter, each creating float objects; `np.dot` runs one loop in optimised C (often using SIMD
        instructions), typically tens to hundreds of times faster. A process pool could at best divide the Python version's time by the number of cores, minus
        overheads, so vectorising wins before parallelism is even considered. Reach for processes when the work cannot be expressed as array operations: parsing,
        string processing, complex per-item logic."""),
    write("A parallel grid search", "medium", tag="ML",
        prompt="""Write `grid_search(evaluate, grid, workers=4)` where `grid` maps parameter names to lists of values and `evaluate(params)` (a top-level function) returns a score
        (higher is better). Evaluate every combination (`itertools.product`, in the order of the grid's keys and values) on a `ProcessPoolExecutor` and return `(best_params,
        results)`, where `results` is a list of `(params, score)` sorted by score descending, ties keeping grid order. A combination whose evaluation raises is left out.""",
        code="""
        import itertools
        from concurrent.futures import ProcessPoolExecutor

        def grid_search(evaluate, grid, workers=4):
            pass
        """,
        tests="""
        def evaluate(params):
            if params["depth"] == 8 and params["lr"] == 0.3:
                raise ValueError("diverged")
            return round(1 - abs(params["lr"] - 0.1) - abs(params["depth"] - 4) / 10, 3)
        best, results = grid_search(evaluate, {"lr": [0.01, 0.1, 0.3], "depth": [2, 4, 8]}, workers=3)
        assert best == {"lr": 0.1, "depth": 4} and len(results) == 8
        assert results[0] == ({"lr": 0.1, "depth": 4}, 1.0) and results[1][1] == 0.91
        assert grid_search(evaluate, {"lr": [0.3], "depth": [8]}) == (None, [])
        """,
        hints=["`keys = list(grid)`; `combos = [dict(zip(keys, values)) for values in itertools.product(*grid.values())]`.",
               "Submit one task per combo, collect `(params, score)` for the ones without an exception, and `sorted(..., key=lambda r: -r[1])` keeps ties stable."],
        solution="""
        import itertools
        from concurrent.futures import ProcessPoolExecutor


        def grid_search(evaluate, grid, workers=4):
            keys = list(grid)
            combos = [dict(zip(keys, values)) for values in itertools.product(*grid.values())]
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [(params, pool.submit(evaluate, params)) for params in combos]
            results = [(params, f.result()) for params, f in futures if f.exception() is None]
            results.sort(key=lambda r: -r[1])
            return (results[0][0] if results else None), results
        """,
        why="""Hyperparameter search is the textbook embarrassingly parallel CPU job: each combination trains and scores independently, so a process pool divides the wall time by
        the number of cores. Parameters travel as small dicts and scores come back as floats, so communication is negligible compared with training. Keeping the
        futures in grid order and sorting with a stable key makes ties reproducible, and failed combinations (a diverging learning rate) are dropped instead of
        aborting the search. Libraries do the same: scikit-learn's `GridSearchCV(n_jobs=-1)` runs fits in worker processes through joblib."""),
)

section("hard", "Hard",
    write("A chunked ordered map with per-item errors", "hard", tag="Data work",
        prompt="""Write `chunked_map(fn, items, workers=4, chunk_size=100)` that behaves like `map(fn, items)` but runs chunks on a `ProcessPoolExecutor`, returning a list of
        `("ok", value)` or `("error", "ExceptionName: message")` per item, in order. `fn` must be a top-level function; write the top-level chunk worker `_run_chunk(fn,
        chunk)` that applies `fn` to each item and catches per-item errors, so one bad item does not fail its whole chunk.""",
        code="""
        from concurrent.futures import ProcessPoolExecutor

        def _run_chunk(fn, chunk):
            pass

        def chunked_map(fn, items, workers=4, chunk_size=100):
            pass
        """,
        tests="""
        def parse_score(text):
            value = float(text)
            if not 0 <= value <= 1:
                raise ValueError(f"out of range: {value}")
            return value
        items = ["0.5", "x", "1.5", "0.25"] * 30
        out = chunked_map(parse_score, items, workers=3, chunk_size=7)
        assert len(out) == 120 and out[:4] == [("ok", 0.5), ("error", "ValueError: could not convert string to float: 'x'"), ("error", "ValueError: out of range: 1.5"), ("ok", 0.25)]
        assert out[4:8] == out[:4] and chunked_map(parse_score, []) == []
        try:
            chunked_map(lambda t: t, ["a"])
            assert False
        except Exception as e:
            assert type(e).__name__ == "PicklingError"
        """,
        hints=["`_run_chunk` returns a list of tuples; wrap each `fn(item)` in `try`.",
               "Submit `_run_chunk(fn, chunk)` per chunk with `pool.map(functools.partial(_run_chunk, fn), chunks)` or `submit`; a pickling failure of `fn` surfaces when you collect the result."],
        solution="""
        from concurrent.futures import ProcessPoolExecutor


        def _run_chunk(fn, chunk):
            out = []
            for item in chunk:
                try:
                    out.append(("ok", fn(item)))
                except Exception as e:
                    out.append(("error", f"{type(e).__name__}: {e}"))
            return out


        def chunked_map(fn, items, workers=4, chunk_size=100):
            chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
            results = []
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_run_chunk, fn, chunk) for chunk in chunks]
                for future in futures:
                    results.extend(future.result())
            return results
        """,
        why="""Error handling must happen **inside** the chunk: if a worker raised on the first bad item, the whole chunk's result would be lost and the caller could not tell which
        of its items succeeded. Returning tagged results per item keeps the output aligned with the input, which matters when results are written back next to the
        records they belong to. The chunk worker and `fn` both travel by name, which is why a lambda fails at submission time with `PicklingError`, before any work
        is done, and `future.result()` re-raises it to the caller: a configuration bug should stop the job, a bad record should not."""),
    write("Choose a chunk size from a cost model", "hard", tag="ML",
        prompt="""Write `pool_time(n, workers, chunk, overhead, item_cost)` returning the modelled wall time of processing `n` items in chunks of `chunk` on `workers` processes: tasks
        are `ceil(n / chunk)`, each task takes `overhead + size * item_cost` (the last task may be smaller), and tasks are assigned in order to the first free worker.
        Then `best_chunk(n, workers, overhead, item_cost, candidates)` returning the candidate with the lowest time (the smallest candidate on ties).""",
        code="""
        import heapq

        def pool_time(n, workers, chunk, overhead, item_cost):
            pass

        def best_chunk(n, workers, overhead, item_cost, candidates):
            pass
        """,
        tests="""
        assert round(pool_time(10_000, 4, 2500, 0.001, 0.00001), 6) == 0.026
        assert round(pool_time(10_000, 4, 1, 0.001, 0.00001), 6) == 2.525
        assert round(pool_time(10, 4, 3, 1.0, 1.0), 6) == 4.0
        assert best_chunk(10_000, 4, 0.001, 0.00001, [1, 10, 100, 1000, 2500, 5000]) == 2500
        assert best_chunk(10_000, 4, 0.0, 0.00001, [1, 100, 2500]) == 1
        assert pool_time(0, 4, 10, 1.0, 1.0) == 0
        """,
        hints=["Build the task durations, then reuse the heap scheduler of 14.1: pop the earliest free worker, push its new finish time.",
               "`min(candidates, key=lambda c: (round(pool_time(...), 12), c))` breaks ties by size."],
        solution="""
        import heapq


        def pool_time(n, workers, chunk, overhead, item_cost):
            sizes = [min(chunk, n - start) for start in range(0, n, chunk)]
            free = [0.0] * workers
            end = 0.0
            for size in sizes:
                start = heapq.heappop(free)
                finish = start + overhead + size * item_cost
                end = max(end, finish)
                heapq.heappush(free, finish)
            return end


        def best_chunk(n, workers, overhead, item_cost, candidates):
            return min(candidates, key=lambda c: (round(pool_time(n, workers, c, overhead, item_cost), 12), c))
        """,
        why="""The model captures the two forces that decide chunk size. Overhead per task pushes towards **large** chunks: with 1-item chunks, 10,000 tasks of 1 ms overhead
        swamp the 10 microseconds of work each. Load balancing pushes towards **enough** chunks to keep every worker busy until the end: with 10 items in chunks of 3 on
        4 workers, the uneven last chunk decides the finish time. With no overhead, the smallest chunks balance best. Real overheads and item costs come from a quick
        measurement on a sample, and the model then picks a sensible `chunksize` without trial and error over the full dataset."""),
    fix("Read the code: CPU-heavy preprocessing on threads", "hard", tag="RAG",
        prompt="""`preprocess_corpus` cleans and chunks documents. It uses a **thread** pool for CPU-bound work, reloads the stop-word list for every document, uses a lambda,
        and sends each document as a separate task. Rewrite it with a `ProcessPoolExecutor`: an `initializer` that loads the stop words once per worker into a global,
        a top-level task function that processes a **chunk** of documents, and results returned in input order. `load_stopwords` must be called once per worker
        (the grader counts the calls), not once per document.""",
        code="""
        from concurrent.futures import ThreadPoolExecutor

        LOADS = []


        def load_stopwords():
            LOADS.append(1)
            return {"the", "a", "of", "to", "is"}


        def clean(doc, stopwords):
            words = [w.strip(".,!?").lower() for w in doc.split()]
            return [w for w in words if w and w not in stopwords]


        def preprocess_corpus(docs, workers=4):
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(lambda d: clean(d, load_stopwords()), docs))
        """,
        tests="""
        import re
        LOADS.clear()
        docs = ["The refund is processed.", "A summary of the policy!", "Refunds to the card"] * 40
        out = preprocess_corpus(docs, workers=2)
        assert out[:3] == [["refund", "processed"], ["summary", "policy"], ["refunds", "card"]] and len(out) == 120
        assert len(LOADS) <= 2
        assert "ProcessPoolExecutor" in __source__ and "lambda" not in __source__ and "initializer" in __source__
        """,
        hints=["`STOPWORDS = None` at module level; `def init_worker(): global STOPWORDS; STOPWORDS = load_stopwords()`.",
               "`def clean_chunk(docs): return [clean(d, STOPWORDS) for d in docs]`, mapped over chunks of, say, 32 documents, then flattened."],
        solution="""
        from concurrent.futures import ProcessPoolExecutor

        LOADS = []
        STOPWORDS = None


        def load_stopwords():
            LOADS.append(1)
            return {"the", "a", "of", "to", "is"}


        def clean(doc, stopwords):
            words = [w.strip(".,!?").lower() for w in doc.split()]
            return [w for w in words if w and w not in stopwords]


        def init_worker():
            global STOPWORDS
            STOPWORDS = load_stopwords()


        def clean_chunk(docs):
            return [clean(d, STOPWORDS) for d in docs]


        def preprocess_corpus(docs, workers=4, chunk_size=32):
            chunks = [docs[i:i + chunk_size] for i in range(0, len(docs), chunk_size)]
            out = []
            with ProcessPoolExecutor(max_workers=workers, initializer=init_worker) as pool:
                for cleaned in pool.map(clean_chunk, chunks):
                    out.extend(cleaned)
            return out
        """,
        why="""Each change applies one rule of this lesson. Cleaning text is pure-Python CPU work, so threads give no speed-up under the GIL and processes are the right tool. The
        stop-word list was loaded 120 times, once per document; the initializer loads it once per worker, which for a real resource (a tokenizer or a spaCy model
        that takes seconds to load) is the difference between minutes and hours. The lambda becomes a top-level function so it can be pickled, and documents travel in
        chunks to amortise per-task overhead. `map` over chunks keeps the output in input order. (On a real machine, `LOADS` would be filled in the workers, not the
        parent; the grader counts them here because this site runs workers in the page.)"""),
    predict("What crosses the process boundary", "hard",
        code="""
        import functools
        from concurrent.futures import ProcessPoolExecutor

        class Model:
            def __init__(self, weights):
                self.weights = weights
            def predict(self, x):
                return sum(w * v for w, v in zip(self.weights, x))

        def apply(model, x):
            return model.predict(x)

        model = Model([0.5, 2.0])
        with ProcessPoolExecutor(2) as pool:
            print(pool.submit(apply, model, [2, 3]).result())
            print(pool.submit(model.predict, [1, 1]).result())
            print(list(pool.map(functools.partial(apply, model), [[1, 0], [0, 1]])))
            print(type(pool.submit(apply, model, (v for v in [1, 2])).exception()).__name__)
            f = pool.submit(lambda: model)
            print(type(f.exception()).__name__)
            g = pool.submit(Model, [1.0])
            print(type(g.result()).__name__, g.result().weights)
        """,
        hints=["Instances of top-level classes pickle with their attributes; bound methods pickle as (instance, method name). Generators are not picklable (list iterators, surprisingly, are)."],
        why="""A `Model` instance of a top-level class pickles with its `weights`, so `apply(model, x)` works, and so does the bound method, which pickles as the instance plus the
        method name; `partial` binds the model for `map`. Each task receives its **own copy** of the model, which is fine for read-only use and wasteful for large
        models (use an initializer instead). A generator argument fails with `TypeError` (a plain list iterator would pickle, generators never do), a lambda with `PicklingError`. Calling the class itself returns a new
        instance, which comes back to the parent by pickling, intact."""),
)

section("interview", "Interview questions",
    explain("When do you use processes instead of threads in Python, and what are the costs?", "medium", tag="Interview",
        why="""Use processes for CPU-bound Python code (parsing, text processing, feature engineering, pure-Python model scoring), because each process has its own interpreter and GIL and
        runs on its own core; use threads (or asyncio) for I/O-bound work, where waiting dominates and threads are cheaper. The costs of processes: start-up time
        (especially with `spawn`), a full interpreter's memory per worker (plus any model loaded in each), and communication by pickling, which requires top-level
        functions and picklable arguments and makes sending large data slow. Mitigations: coarse tasks with chunking, initializers to load resources once per worker,
        sending paths or ids instead of data, shared memory for large arrays, and the `__main__` guard. Before either, vectorise with NumPy or use libraries that
        already parallelise internally; and note that free-threaded Python makes threads viable for CPU work when the libraries support it."""),
    explain("Why do scripts that use multiprocessing need `if __name__ == \"__main__\":`?", "medium", tag="Interview",
        why="""With the `spawn` start method (the default on Windows and macOS) and `forkserver` (the Linux default since Python 3.14), each worker starts a fresh interpreter that
        **imports the main script as a module** to find the functions it must run. Everything at the top level of the script runs again in every worker during that
        import. If the top level creates a process pool or starts the job, each worker would try to do the same, which would recurse; Python detects this and raises
        an error about starting a new process before bootstrapping finished. Putting the entry-point code under `if __name__ == "__main__":` makes it run only when the
        file is executed directly, since imported modules have their own name. Keep worker functions and classes at the top level so they can be found by name, and
        avoid expensive work at import time."""),
    explain("You need to preprocess 50 million documents on one 32-core machine. How do you design it?", "hard", tag="Interview",
        why="""Profile a sample first to find the per-document cost and whether it is CPU-bound (likely: cleaning, tokenising, chunking). Store the input in shards (many files or
        row ranges), and process **shards** as tasks in a `ProcessPoolExecutor` with about 32 workers (fewer if memory per worker is large): each task receives a shard
        path, streams it, and writes its output shard itself (JSONL or Parquet), returning only counts and error summaries, so almost nothing crosses the process boundary.
        Load tokenizers or models once per worker with an initializer. Make it resumable and idempotent: one output file per input shard written atomically, so a
        restarted job skips finished shards, and a manifest records counts and failures (12.P). Handle bad documents inside the task (quarantine and count them).
        Track progress with `as_completed`. Check where the remaining serial parts are (reading a single compressed file, a final merge) using Amdahl's law, and consider
        vectorised libraries (pandas, Polars, Arrow compute) or a distributed engine (Spark, Ray, Dask) if one machine is not enough."""),
)

recap(
    "`ProcessPoolExecutor` runs tasks in separate processes, each with its own GIL, so CPU-bound Python code runs in parallel; size it to the number of cores.",
    "Everything sent is pickled: only top-level functions and classes, `partial`s of them, and picklable arguments and results; lambdas and generators fail.",
    "Guard entry-point code with `if __name__ == \"__main__\":` because `spawn` and `forkserver` workers import your script.",
    "Make tasks coarse with chunks or `chunksize`, load resources once per worker with `initializer`, and send paths or ids rather than data.",
    "Vectorise with NumPy before parallelising, and measure: overheads can make a pool slower than a loop.",
)
