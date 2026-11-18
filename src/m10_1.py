from lesson import *
from diagrams import *

lesson(
    id="m10-1", num="10.1", title="Iterator classes",
    intro="Writing your own iterables and iterators: the protocol by hand with `__iter__` and `__next__`, the difference "
          "between a re-iterable container and a one-shot iterator, generators as the easy way to implement `__iter__`, "
          "the two-argument `iter()`, peeking, and the traps: exhausted iterators, `StopIteration` leaking out of "
          "generators, and changing a collection while looping. Applied to pagination, batching, windows and token streams.",
    desc="`__iter__` and `__next__` by hand, and when a generator is better.",
    keys="iterator iterable __iter__ __next__ stopiteration protocol re-iterable one-shot generator pep 479 iter sentinel peekable pagination cursor batch sliding window round robin lazy",
)

term("Iterable", "An object with `__iter__` that returns a new iterator each time it is called, so it can be looped over many times.")
term("Iterator", "An object with `__next__` (returning the next item or raising `StopIteration`) and an `__iter__` that returns itself.")
term("Sentinel", "A special value that marks the end of a stream, such as `b\"\"` from `read()`; `iter(func, sentinel)` calls `func` until it appears.")

section("protocol", "The protocol, by hand",
    fig(stage_map(10, "a streaming export job"), "Module 10 at a glance: writing iterators and context managers yourself, building up to a job that streams data and always cleans up."),
    fig(chain(["iter(obj)", "calls obj.__iter__()", "next(it) calls|it.__next__()", ("StopIteration|ends the loop", "accent")]),
        "The iterator protocol is two methods: `__iter__` returns an iterator, and the iterator's `__next__` returns values until it raises `StopIteration`."),
    p("""Lesson 6.3 showed what a `for` loop does: it calls `iter(obj)` once to get an **iterator**, then `next(iterator)` repeatedly until
    `StopIteration` is raised. In terms of the data model (9.2), `iter(obj)` calls `obj.__iter__()` and `next(it)` calls `it.__next__()`. So
    to make your own objects work with `for`, `list()`, `sum()`, unpacking and comprehensions, you implement those two methods. An
    **iterator** class keeps the position of the walk as state: `__next__` returns the next item and advances, or raises `StopIteration`
    when there is nothing left; its `__iter__` returns `self`, so an iterator can be used wherever an iterable is expected."""),
    ex("""
    class Countdown:
        \"\"\"An iterator: it remembers where it is.\"\"\"

        def __init__(self, start):
            self.current = start

        def __iter__(self):
            return self

        def __next__(self):
            if self.current <= 0:
                raise StopIteration
            value = self.current
            self.current -= 1
            return value

    c = Countdown(3)
    print(next(c), next(c), list(c), list(c))
    print(sum(Countdown(4)), [x * 10 for x in Countdown(2)], max(Countdown(5)))
    """, "by_hand.py"),
    p("""`next(c)` twice takes 3 and 2; `list(c)` drains what is left, 1; and a second `list(c)` gets nothing, because the iterator's state is
    exhausted and nothing resets it. That is the defining property of an iterator: **one pass**. Raising `StopIteration` is the only correct
    way to say "no more items"; returning `None` would be treated as an item, and a loop would never end."""),
)

section("iterable", "Iterable containers and one-shot iterators",
    fig(table(["", "iterable container", "one-shot iterator"], [
        ["__iter__ returns", "a new iterator each time", "itself"],
        ["has __next__", "no", "yes"],
        ["second for loop", "runs again from the start", "finds nothing"],
        ["examples", "list, dict, range, your container", "file, generator, map()"],
    ], hl={(2, 2)}, label="iterables versus iterators"),
        "Containers hand out fresh iterators, so they can be looped over many times; an iterator is consumed once."),
    p("""A list can be looped over any number of times because it is not an iterator itself: each `iter(my_list)` creates a **new** list
    iterator starting at the beginning. Your container classes should work the same way. Their `__iter__` must return a **fresh**
    iterator each time, not `self`, so that two loops (or a nested loop over the same object) each get their own position. Making a
    container its own iterator is a classic bug: the second loop silently sees nothing (problem 3)."""),
    p("""There are therefore two separate roles, often played by two classes: the **iterable** (the container, holding the data, with an
    `__iter__` that builds an iterator) and the **iterator** (a lightweight object holding only a reference to the data and a position).
    Python's built-ins follow this split: `list` and `list_iterator`, `dict` and `dict_keyiterator`, `range` and `range_iterator`."""),
    ex("""
    class Playlist:
        def __init__(self, songs):
            self._songs = list(songs)

        def __iter__(self):
            return PlaylistIterator(self._songs)     # a new iterator every time

    class PlaylistIterator:
        def __init__(self, songs):
            self._songs = songs
            self._i = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._i >= len(self._songs):
                raise StopIteration
            song = self._songs[self._i]
            self._i += 1
            return song

    p = Playlist(["intro", "verse", "outro"])
    print(list(p), list(p))
    print([(a, b) for a in p for b in p if a < b][:3])     # nested loops need independent iterators
    it = iter(p)
    print(next(it), iter(it) is it, iter(p) is iter(p))
    """, "iterable_vs_iterator.py"),
)

section("generators", "Generators: the easy way to write `__iter__`",
    p("""Writing a separate iterator class is a lot of ceremony for "walk my items". A generator function returns a new generator, which is an
    iterator, every time it is called (6.3), so making `__iter__` itself a generator gives you exactly the fresh-iterator behaviour of a
    container, with the position and the `StopIteration` handled for you. In most code this is the right way to make a class iterable."""),
    ex("""
    class Playlist:
        def __init__(self, songs):
            self._songs = list(songs)

        def __iter__(self):
            for song in self._songs:          # or simply: yield from self._songs
                yield song

        def __len__(self):
            return len(self._songs)

    class Dataset:
        def __init__(self, rows):
            self._rows = rows

        def __iter__(self):
            for row in self._rows:
                if row.get("label") is not None:     # iteration can filter or transform lazily
                    yield row["text"], row["label"]

    p = Playlist(["intro", "verse"])
    print(list(p), list(p), len(p))
    d = Dataset([{"text": "win now", "label": 1}, {"text": "?", "label": None}, {"text": "lunch", "label": 0}])
    print(list(d), dict(d))
    """, "generator_iter.py"),
    p("""Write a class with `__next__` by hand when the iterator needs **more than iteration**: extra methods such as `peek()` or `close()`,
    state that callers inspect while iterating (how many pages fetched, the text accumulated so far), or a way to be passed around and
    resumed by several consumers. Otherwise, a generator method is shorter, harder to get wrong, and faster (problem 8)."""),
)

section("tools", "Useful forms: `iter(callable, sentinel)` and peeking",
    p("""`iter()` has a second form: `iter(func, sentinel)` creates an iterator that calls `func()` with no arguments on every step and stops
    when the result equals `sentinel`. It turns "call this until it returns the end marker" into a loop, and the classic use is reading a
    binary stream in fixed-size chunks: `iter(lambda: f.read(8192), b"")` yields chunks until `read` returns empty bytes. Combined with
    `functools.partial`, it reads queues, sockets and paginated APIs in the same way."""),
    ex("""
    import io
    from functools import partial

    stream = io.BytesIO(b"abcdefghij")
    print(list(iter(partial(stream.read, 4), b"")))

    queue = ["job1", "job2", "STOP", "job3"]
    for job in iter(lambda: queue.pop(0), "STOP"):
        print("processing", job)
    print("left in queue:", queue)
    """, "iter_sentinel.py"),
    p("""Another common need is to **look at the next item without consuming it**: a parser deciding what to do based on the next token, a merge
    step comparing heads of streams. Plain iterators cannot do that, so a small wrapper class keeps one item in a buffer: `peek()` fills the
    buffer if needed and returns it; `__next__` returns the buffered item first. Because it needs an extra method, this is a case where a
    hand-written iterator class is the right tool (problem 7)."""),
)

section("lazy", "Lazy objects: computing on demand",
    p("""An iterable does not have to hold its items. `range(10**12)` uses almost no memory because it computes each number when asked. Your
    classes can do the same: a **paginated API client** fetches one page of results at a time while the caller loops, and stops fetching as
    soon as the caller stops; a **sliding window** over a token list computes each window on the fly; a dataset reads rows from disk as they
    are needed. Laziness means the first item is available immediately and memory does not grow with the total size (problem 5)."""),
    ex("""
    class Pages:
        \"\"\"Iterate over all items of a paginated API, fetching pages only as needed.\"\"\"

        def __init__(self, fetch):
            self.fetch = fetch                 # fetch(cursor) -> (items, next_cursor or None)
            self.pages_fetched = 0

        def __iter__(self):
            cursor = None
            while True:
                items, cursor = self.fetch(cursor)
                self.pages_fetched += 1
                yield from items
                if cursor is None:
                    return

    DATA = {None: (["a", "b"], "p2"), "p2": (["c", "d"], "p3"), "p3": (["e"], None)}
    pages = Pages(lambda cursor: DATA[cursor])
    print(list(pages), pages.pages_fetched)
    pages.pages_fetched = 0
    first_three = []
    for item in pages:
        first_three.append(item)
        if len(first_three) == 3:
            break
    print(first_three, pages.pages_fetched)
    """, "lazy_pages.py"),
    p("""Stopping after three items fetched only two pages, because the generator inside `__iter__` was simply never resumed. A lazy class can
    still offer `__len__` when the length can be computed without iterating (a window count from the list length, 9.2); if it cannot, it
    should not pretend, since `len()` is expected to be cheap."""),
)

section("traps", "Iteration traps",
    fig(chain(["it = iter(data)", "first pass consumes it", ("second pass:|silently empty", "bad")]),
        "The commonest iteration bug: reusing an exhausted iterator gives no error, just no items."),
    p("""**`StopIteration` inside a generator.** Calling `next(it)` without a default inside a generator body, when `it` is exhausted, raises
    `StopIteration` inside the generator. Before Python 3.7 that silently ended the generator; since PEP 479 it is turned into a
    `RuntimeError: generator raised StopIteration`, because silently ending hid bugs. Use `next(it, default)` or catch `StopIteration`
    explicitly and `return` (problem 6)."""),
    ex("""
    def pairs(items):
        it = iter(items)
        for first in it:
            second = next(it)            # raises StopIteration when the length is odd
            yield first, second

    def safe_pairs(items):
        it = iter(items)
        for first in it:
            second = next(it, None)
            yield first, second

    print(list(safe_pairs([1, 2, 3])))
    try:
        list(pairs([1, 2, 3]))
    except RuntimeError as e:
        print("RuntimeError:", e)
    """, "pep479.py"),
    p("""**Changing what you are iterating.** Adding to or removing from a list while looping over it skips or repeats items (2.2), and changing
    a dict's or set's size during iteration raises `RuntimeError: dictionary changed size during iteration`. Iterate over a copy
    (`list(d)`) or collect changes and apply them after the loop. Your own iterators should either detect such changes or document that the
    underlying data must not change during iteration (problem 12)."""),
    p("""**Sharing one iterator.** Two consumers of the same iterator split its items between them, which is sometimes the point (`zip(it, it)`,
    6.4) and usually a bug. Hand each consumer its own iterator from the iterable, or use `itertools.tee` if the source can only be read
    once."""),
)

section("warmup", "Warm-up",
    predict("An iterator by hand", "easy",
        code="""
        class Evens:
            def __init__(self, limit):
                self.n = 0
                self.limit = limit
            def __iter__(self):
                return self
            def __next__(self):
                if self.n > self.limit:
                    raise StopIteration
                value = self.n
                self.n += 2
                return value

        e = Evens(6)
        print(next(e), next(e), list(e))
        print(list(e), next(e, "done"), list(Evens(3)))
        a, b, *rest = Evens(10)
        print(a, b, rest)
        """,
        hints=["An iterator's state is consumed by every `next`, `list` or loop; nothing resets it."],
        why="""`next` takes 0 and 2, and `list` drains the rest up to the limit: 4 and 6. A second `list` finds the iterator exhausted, and `next` with a
        default returns the default instead of raising. A fresh `Evens(3)` yields 0 and 2. Unpacking works with any iterable, including your
        own: two names take the first items and `*rest` collects the remainder."""),
    write("A re-iterable range of dates", "easy", tag="Data work",
        prompt="""Write a class `DayRange(start, end)` (both `datetime.date`, end inclusive) that can be iterated **any number of times**, yielding each
        date in order, with `__len__` (number of days, 0 if `end < start`), `__contains__` for dates (computed without iterating) and a
        `__repr__` like `DayRange(2025-01-30, 2025-02-02)`. Use a generator for `__iter__`.""",
        code="""
        import datetime as dt

        class DayRange:
            pass
        """,
        tests="""
        import datetime as dt
        r = DayRange(dt.date(2025, 1, 30), dt.date(2025, 2, 2))
        days = [d.isoformat() for d in r]
        assert days == ["2025-01-30", "2025-01-31", "2025-02-01", "2025-02-02"] and [d.day for d in r] == [30, 31, 1, 2]
        assert len(r) == 4 and dt.date(2025, 2, 1) in r and dt.date(2025, 2, 3) not in r
        assert repr(r) == "DayRange(2025-01-30, 2025-02-02)" and len(DayRange(dt.date(2025, 1, 2), dt.date(2025, 1, 1))) == 0
        assert list(DayRange(dt.date(2025, 1, 2), dt.date(2025, 1, 1))) == []
        """,
        hints=["`end - start` is a `timedelta`; `.days + 1` is the count. Step with `start + dt.timedelta(days=i)` (5.3)."],
        solution="""
        import datetime as dt

        class DayRange:
            def __init__(self, start, end):
                self.start = start
                self.end = end

            def __len__(self):
                return max(0, (self.end - self.start).days + 1)

            def __iter__(self):
                for i in range(len(self)):
                    yield self.start + dt.timedelta(days=i)

            def __contains__(self, day):
                return self.start <= day <= self.end

            def __repr__(self):
                return f"DayRange({self.start}, {self.end})"
        """,
        why="""Because `__iter__` is a generator function, every loop gets a new generator starting at day 0, so the range can be iterated twice, as the test
        does. The dates are computed on demand, like `range`, so a range of ten years costs nothing until it is used. `__contains__` answers
        with two comparisons instead of walking every day, which is what `in` would do by default (9.2). Month and year boundaries are
        handled by `timedelta` arithmetic, never by hand. Date ranges like this drive backfills and daily evaluation jobs."""),
    fix("A collection that can be looped over only once", "easy", tag="ML",
        prompt="""`Vocabulary` returns itself from `__iter__` and keeps the position in an attribute, so the second loop over the same vocabulary is
        empty, and a nested loop stops early. Fix it so every loop gets an independent pass.""",
        code="""
        class Vocabulary:
            def __init__(self, words):
                self.words = sorted(set(words))
                self._i = 0

            def __iter__(self):
                return self

            def __next__(self):
                if self._i >= len(self.words):
                    raise StopIteration
                word = self.words[self._i]
                self._i += 1
                return word
        """,
        tests="""
        v = Vocabulary(["refund", "policy", "refund", "window"])
        assert list(v) == ["policy", "refund", "window"] and list(v) == ["policy", "refund", "window"]
        pairs = [(a, b) for a in v for b in v if a < b]
        assert pairs == [("policy", "refund"), ("policy", "window"), ("refund", "window")]
        assert len(list(v)) == 3
        """,
        hints=["Make `__iter__` a generator over `self.words`, and remove `__next__` and `_i`."],
        solution="""
        class Vocabulary:
            def __init__(self, words):
                self.words = sorted(set(words))

            def __iter__(self):
                yield from self.words
        """,
        why="""Returning `self` made the container its own iterator, with one shared position: after the first full loop `_i` stayed at the end, so every
        later loop was empty, and in the nested comprehension the inner loop consumed the same position as the outer one. A container must hand
        out a new iterator per loop; a generator `__iter__` does that automatically, since each call creates a fresh generator. Having fewer
        methods also means there is no state to get out of sync."""),
    predict("Iterating until a sentinel", "easy",
        code="""
        import io
        from functools import partial

        data = io.BytesIO(b"0123456789AB")
        print([c.decode() for c in iter(partial(data.read, 5), b"")])
        lines = iter(["header", "a", "b", "", "ignored"])
        print(list(iter(lambda: next(lines), "")))
        counter = iter([3, 2, 1, 0, -1])
        print(list(iter(counter.__next__, 0)), list(counter))
        """,
        hints=["`iter(func, sentinel)` calls `func()` repeatedly and stops, without yielding it, when the result equals the sentinel."],
        why="""Reading five bytes at a time gives two full chunks and a shorter last one; the next read returns `b""`, the sentinel, which ends the loop. The
        second loop stops at the empty line, so `"ignored"` is never read. With the counter, the loop stops when it reads 0, which consumes the 0;
        the `-1` is still in the underlying iterator afterwards."""),
)

section("medium", "Medium",
    write("Paginate a search API lazily", "medium", tag="GenAI",
        prompt="""Write a class `SearchResults(fetch, page_size)` where `fetch(offset, limit)` returns a list of up to `limit` results starting at `offset`
        (an empty or short list means the end). Iterating yields results one by one, fetching pages only when needed; record every `fetch` call's
        offset in `self.offsets`. It must be re-iterable (a new loop starts again from offset 0). Add `first(n)` returning the first `n` results
        without fetching more pages than necessary.""",
        code="""
        class SearchResults:
            pass
        """,
        tests="""
        DATA = [f"doc{i}" for i in range(7)]
        def fetch(offset, limit):
            return DATA[offset:offset + limit]

        r = SearchResults(fetch, page_size=3)
        assert list(r) == DATA and r.offsets == [0, 3, 6]
        r.offsets = []
        assert r.first(4) == ["doc0", "doc1", "doc2", "doc3"] and r.offsets == [0, 3]
        r.offsets = []
        assert list(r) == DATA and r.offsets == [0, 3, 6]
        exact = SearchResults(lambda o, l: [f"x{i}" for i in range(6)][o:o + l], page_size=3)
        assert list(exact) == ["x0", "x1", "x2", "x3", "x4", "x5"] and exact.offsets == [0, 3, 6]
        """,
        hints=["Make `__iter__` a generator: loop fetching pages, `yield from page`, stop when the page is shorter than `page_size`.",
               "`first(n)` can use `itertools.islice(self, n)` (6.4), which stops pulling from the generator after `n` items."],
        solution="""
        from itertools import islice

        class SearchResults:
            def __init__(self, fetch, page_size):
                self.fetch = fetch
                self.page_size = page_size
                self.offsets = []

            def __iter__(self):
                offset = 0
                while True:
                    self.offsets.append(offset)
                    page = self.fetch(offset, self.page_size)
                    yield from page
                    if len(page) < self.page_size:
                        return
                    offset += self.page_size

            def first(self, n):
                return list(islice(self, n))
        """,
        why="""The generator fetches a page, hands its results out one at a time, and fetches the next page only when the consumer asks for more, so
        `first(4)` stops after two pages: `islice` simply stops pulling. A short page signals the end; when the total is an exact multiple of the
        page size, one extra fetch returns an empty page, which is unavoidable without a total count (the last test). Each `for` loop gets a
        new generator starting at offset 0, so the object is re-iterable. Vector database clients, Slack and GitHub API wrappers, and
        `boto3` paginators expose large result sets exactly this way."""),
    fix("A generator that dies with RuntimeError", "medium", tag="Data work",
        prompt="""`key_values(tokens)` turns a flat list `[k1, v1, k2, v2, ...]` into pairs. With an odd number of tokens it crashes with
        `RuntimeError: generator raised StopIteration`. Fix it so a trailing key gets the value `None`.""",
        code="""
        def key_values(tokens):
            it = iter(tokens)
            for key in it:
                value = next(it)
                yield key, value
        """,
        tests="""
        assert list(key_values(["model", "small", "temperature", "0.2"])) == [("model", "small"), ("temperature", "0.2")]
        assert list(key_values(["a", 1, "b"])) == [("a", 1), ("b", None)]
        assert list(key_values([])) == []
        """,
        hints=["`next(it, None)` returns `None` instead of raising when the iterator is exhausted."],
        solution="""
        def key_values(tokens):
            it = iter(tokens)
            for key in it:
                value = next(it, None)
                yield key, value
        """,
        why="""Inside a generator, an exhausted `next(it)` raises `StopIteration` from the generator's own body. Since Python 3.7 (PEP 479), Python converts
        that into a `RuntimeError`, because silently ending the generator early used to hide real bugs: the caller would just see fewer items.
        `next(it, default)` handles "no more items" explicitly. Note that `for key in it` and `next(it)` share one iterator on purpose: each step
        of the loop takes a key, and `next` takes the value after it, the pairing idiom of 6.4."""),
    write("A peekable iterator", "medium", tag="Data work",
        prompt="""Write a class `Peekable(iterable)` that is an iterator (with `__iter__` and `__next__`) and also has `peek(default=...)` returning the
        next item **without consuming it** (if the iterator is exhausted, return `default` when given, otherwise raise `StopIteration`). Add
        `__bool__`, true while items remain. It must work on any iterable, including generators, and must not read ahead more than one item.""",
        code="""
        class Peekable:
            pass
        """,
        tests="""
        read = []
        def source():
            for x in ["a", "b", "c"]:
                read.append(x)
                yield x

        p = Peekable(source())
        assert p.peek() == "a" and p.peek() == "a" and read == ["a"]
        assert next(p) == "a" and next(p) == "b" and bool(p) and read == ["a", "b", "c"]
        assert list(p) == ["c"] and not p and p.peek("end") == "end"
        try:
            p.peek()
            assert False
        except StopIteration:
            pass
        try:
            next(p)
            assert False
        except StopIteration:
            pass
        assert list(Peekable([])) == [] and iter(p) is p
        """,
        hints=["Keep `self._buffer` as an empty list or a list with one item. `peek` fills it with `next(self._it)` if empty.",
               "Use a private sentinel object to tell \"no default given\" from `default=None` (2.1)."],
        solution="""
        _MISSING = object()


        class Peekable:
            def __init__(self, iterable):
                self._it = iter(iterable)
                self._buffer = []

            def __iter__(self):
                return self

            def __next__(self):
                if self._buffer:
                    return self._buffer.pop()
                return next(self._it)

            def peek(self, default=_MISSING):
                if not self._buffer:
                    try:
                        self._buffer.append(next(self._it))
                    except StopIteration:
                        if default is _MISSING:
                            raise
                        return default
                return self._buffer[0]

            def __bool__(self):
                try:
                    self.peek()
                except StopIteration:
                    return False
                return True
        """,
        why="""Peeking needs state that survives between calls (the buffered item) and an extra method, so this is a job for an iterator class rather than a
        generator. The buffer holds at most one item, and `next` drains it first, so the order of items is preserved and the source is never
        read more than one item ahead, which the `read` list checks; that matters when the source is a network stream. `__bool__` peeks to
        answer "anything left?". The sentinel default distinguishes `peek()` (raise) from `peek(None)` (return `None`). The `more-itertools`
        package ships this as `peekable`, which parsers and tokenisers use constantly."""),
    choose("A hand-written iterator or a generator", "medium",
        prompt="Both produce the squares of 0 to 299,999 and sum them. Which is faster?",
        setup="""class Squares:
    def __init__(self, n):
        self.n = n
        self.i = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        value = self.i * self.i
        self.i += 1
        return value

def squares(n):
    for i in range(n):
        yield i * i""",
        options={
            "a": "total = sum(Squares(300_000))",
            "b": "total = sum(squares(300_000))",
        },
        answer="b",
        hints=["What does each step of the class-based iterator cost compared with resuming a generator?"],
        why="""Every step of the class iterator is a full method call into `__next__`, with attribute reads and writes on `self` (`self.i`, `self.n`) and
        a comparison done in Python. The generator keeps its state in local variables of a suspended frame, and resuming it is cheaper than a
        method call; the loop counter comes from `range`, implemented in C. The generator is also shorter and cannot forget `StopIteration`.
        Write the class only when the iterator needs extra methods or inspectable state."""),
    trace("Independent and shared iterators", "medium",
        prompt="Fill in `a`, `b` and `rest` after each marked line.",
        code="""
        class Box:
            def __init__(self, items):
                self.items = items
            def __iter__(self):
                yield from self.items

        box = Box([1, 2, 3, 4])
        i1, i2 = iter(box), iter(box)
        a, b, rest = next(i1), next(i2), None  # row: "two iterators"
        a, b, rest = next(i1), next(i1), list(i2)  # row: "advance i1, drain i2"
        shared = iter(box)
        a, b, rest = next(shared), next(shared), list(zip(shared, shared))  # row: "one shared iterator"
        """,
        trace_vars=["a", "b", "rest"],
        hints=["Each `iter(box)` starts a new generator. `zip(shared, shared)` pulls from the same iterator for both slots."],
        why="""`iter(box)` creates a new generator each time, so `i1` and `i2` both start at 1. Advancing `i1` twice gives 2 and 3, while draining `i2`
        continues from its own position. One shared iterator splits its items among all its consumers: after two `next` calls only 3 and 4 remain,
        and `zip` pairs them with each other."""),
    fix("Batches that lose the last items", "medium", tag="ML",
        prompt="""`Batches(rows, size)` should yield lists of `size` rows and a final shorter batch, and be iterable many times (one pass per training
        epoch). It drops the last partial batch, and the second epoch is empty. Fix it.""",
        code="""
        class Batches:
            def __init__(self, rows, size):
                self.rows = list(rows)
                self.size = size
                self.pos = 0

            def __iter__(self):
                return self

            def __next__(self):
                if self.pos + self.size > len(self.rows):
                    raise StopIteration
                batch = self.rows[self.pos:self.pos + self.size]
                self.pos += self.size
                return batch

            def __len__(self):
                return len(self.rows) // self.size
        """,
        tests="""
        b = Batches(range(7), 3)
        assert list(b) == [[0, 1, 2], [3, 4, 5], [6]] and len(b) == 3
        epochs = [sum(len(batch) for batch in b) for _ in range(3)]
        assert epochs == [7, 7, 7]
        assert list(Batches([], 4)) == [] and len(Batches([], 4)) == 0 and len(Batches(range(6), 3)) == 2
        """,
        hints=["Make `__iter__` a generator over `range(0, len(self.rows), self.size)` (6.1); drop `pos` and `__next__`.",
               "The number of batches is a ceiling division: `-(-n // size)` or `(n + size - 1) // size`."],
        solution="""
        class Batches:
            def __init__(self, rows, size):
                if size < 1:
                    raise ValueError("size must be at least 1")
                self.rows = list(rows)
                self.size = size

            def __iter__(self):
                for start in range(0, len(self.rows), self.size):
                    yield self.rows[start:start + self.size]

            def __len__(self):
                return (len(self.rows) + self.size - 1) // self.size
        """,
        why="""Two bugs. The end test `pos + size > len(rows)` refused to produce a batch unless a **full** one fitted, so the last row was silently never
        trained on, and `__len__` used floor division and agreed with the bug. And the object was its own iterator, so after the first epoch
        `pos` stayed at the end and every later epoch iterated nothing, which in a training loop looks like "the model stopped improving".
        Generating batches with a stepped `range` and slices (which stop safely at the end) fixes both, and `__len__` now uses ceiling
        division, so progress bars and learning-rate schedules based on `len(batches)` are right. PyTorch's `DataLoader` has a `drop_last`
        option precisely because dropping the partial batch should be a choice, not an accident."""),
    write("Sliding windows with a length", "medium", tag="RAG",
        prompt="""Write a class `Windows(tokens, size, stride)` that yields overlapping windows (lists) of `size` tokens starting every `stride` tokens,
        plus a final window aligned to the end if the last regular window does not reach it (as in 6.1). It must be re-iterable, never build the
        whole list of windows, and have a `__len__` computed **arithmetically** (no iteration). Fewer than `size` tokens give one window with all
        of them (none for an empty list). Validate `1 <= stride <= size`.""",
        code="""
        class Windows:
            pass
        """,
        tests="""
        t = list(range(10))
        w = Windows(t, 4, 3)
        assert list(w) == [[0, 1, 2, 3], [3, 4, 5, 6], [6, 7, 8, 9]] and len(w) == 3
        w2 = Windows(t, 4, 2)
        assert list(w2) == [[0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 7], [6, 7, 8, 9]] and len(w2) == 4
        w3 = Windows(t, 6, 6)
        assert list(w3) == [[0, 1, 2, 3, 4, 5], [4, 5, 6, 7, 8, 9]] and len(w3) == 2 and list(w3) == list(w3)
        assert list(Windows([1, 2], 5, 1)) == [[1, 2]] and len(Windows([1, 2], 5, 1)) == 1 and len(Windows([], 3, 1)) == 0
        for bad in [(4, 0), (4, 5)]:
            try:
                Windows(t, *bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["Regular window starts: `range(0, n - size + 1, stride)`, whose length you can take with `len(range(...))` without iterating.",
               "There is an extra final window when the last regular start plus `size` is less than `n`."],
        solution="""
        class Windows:
            def __init__(self, tokens, size, stride):
                if not 1 <= stride <= size:
                    raise ValueError("need 1 <= stride <= size")
                self.tokens = list(tokens)
                self.size = size
                self.stride = stride

            def _starts(self):
                return range(0, len(self.tokens) - self.size + 1, self.stride)

            def __len__(self):
                n = len(self.tokens)
                if n == 0:
                    return 0
                if n <= self.size:
                    return 1
                starts = self._starts()
                return len(starts) + (starts[-1] + self.size < n)

            def __iter__(self):
                n = len(self.tokens)
                if n == 0:
                    return
                if n <= self.size:
                    yield list(self.tokens)
                    return
                starts = self._starts()
                for s in starts:
                    yield self.tokens[s:s + self.size]
                if starts[-1] + self.size < n:
                    yield self.tokens[-self.size:]
        """,
        why="""The windows are computed lazily, one slice per step, so a long document never has all its windows in memory at once; the generator
        `__iter__` makes the object re-iterable. `len()` is answered by arithmetic on a `range` object (whose own `len` and indexing are O(1)),
        plus one for the end-aligned window, so it is cheap and always agrees with the iteration, which the tests check case by case. The
        boolean in `len(starts) + (condition)` counts as 0 or 1. Embedding pipelines use the length to size progress bars and to batch
        requests before reading any window."""),
    predict("Changing collections while iterating", "medium",
        code="""
        nums = [1, 2, 3, 4, 5, 6]
        for n in nums:
            if n % 2 == 0:
                nums.remove(n)
        print(nums)

        scores = {"a": 1, "b": 0, "c": 2}
        try:
            for k in scores:
                if scores[k] == 0:
                    del scores[k]
        except RuntimeError as e:
            print("RuntimeError:", e)

        scores = {"a": 1, "b": 0, "c": 2}
        for k in list(scores):
            if scores[k] == 0:
                del scores[k]
        print(scores)
        """,
        hints=["Removing from a list shifts later items under the loop's index. Dicts check their size during iteration."],
        why="""Here removing the even numbers happens to work: each removal shifts the list, the loop skips the item after the removed one, and that item
        is odd every time, so nothing even is missed. With other data the same loop skips items (2.2), so it is never a safe pattern. The dict
        detects the change and raises `RuntimeError` rather than iterating over a structure that has been reorganised. Iterating over a
        **copy** of the keys (`list(scores)`) makes the deletion safe."""),
)

section("hard", "Hard",
    write("Round-robin over several streams", "hard", tag="Data work",
        prompt="""Write an iterator class `RoundRobin(*iterables)` that yields one item from each iterable in turn (`a1, b1, c1, a2, b2, ...`), skipping
        iterables as they run out, until all are exhausted. It must work with generators and infinite iterables (it must not read ahead), and
        expose `active`, the number of iterables not yet exhausted.""",
        code="""
        from collections import deque

        class RoundRobin:
            pass
        """,
        tests="""
        assert list(RoundRobin("ABC", "D", "EF")) == ["A", "D", "E", "B", "F", "C"]
        assert list(RoundRobin()) == [] and list(RoundRobin([], [1])) == [1]
        import itertools
        rr = RoundRobin(itertools.count(), "xy")
        assert [next(rr) for _ in range(6)] == [0, "x", 1, "y", 2, 3] and rr.active == 1
        r2 = RoundRobin([1, 2], [3])
        assert r2.active == 2
        list(r2)
        assert r2.active == 0 and iter(r2) is r2
        """,
        hints=["Keep a `deque` of iterators. `__next__` pops one from the left, tries `next` on it, and appends it back on the right if it produced an item.",
               "If it is exhausted, drop it and try the next; raise `StopIteration` when the deque is empty."],
        solution="""
        from collections import deque

        class RoundRobin:
            def __init__(self, *iterables):
                self._queue = deque(iter(it) for it in iterables)

            @property
            def active(self):
                return len(self._queue)

            def __iter__(self):
                return self

            def __next__(self):
                while self._queue:
                    it = self._queue.popleft()
                    try:
                        item = next(it)
                    except StopIteration:
                        continue
                    self._queue.append(it)
                    return item
                raise StopIteration
        """,
        why="""A deque of iterators rotates in O(1): take the front one, get one item, put it at the back, which produces the round-robin order. An exhausted
        iterator is simply not put back, so `active` (a property over the deque's length, 9.3) shrinks as streams end. Because each step pulls
        exactly one item from exactly one iterator, infinite sources work and nothing is read ahead. Interleaving like this is used to mix
        training data sources fairly, to merge results from several retrievers, and in schedulers that give tasks equal turns. A generator
        could produce the same order, but the class exposes `active` while iterating."""),
    fix("Read the code: a line reader", "hard", tag="Data work",
        prompt="""`LineReader(text)` should iterate over the non-blank lines of a text (stripped), any number of times, number them from 1 in `numbered()`,
        and report `len()` without consuming anything. The second loop is empty, `numbered()` starts at 0 and skips the first line, and `len()`
        consumes the lines. Read it, find the bugs and fix them.""",
        code="""
        class LineReader:
            def __init__(self, text):
                self._lines = iter(text.splitlines())

            def __iter__(self):
                return self

            def __next__(self):
                line = next(self._lines)
                while not line.strip():
                    line = next(self._lines)
                return line.strip()

            def numbered(self):
                next(self)
                return [(i, line) for i, line in enumerate(self)]

            def __len__(self):
                return sum(1 for _ in self)
        """,
        tests="""
        text = "first line\\n\\n  second line  \\n   \\nthird"
        r = LineReader(text)
        assert len(r) == 3 and list(r) == ["first line", "second line", "third"]
        assert list(r) == ["first line", "second line", "third"]
        assert r.numbered() == [(1, "first line"), (2, "second line"), (3, "third")]
        assert len(LineReader("")) == 0 and list(LineReader("\\n \\n")) == []
        """,
        hints=["Storing `iter(...)` in `__init__` makes the object one-shot. Store the list of cleaned lines instead.",
               "`numbered` should use `enumerate(self, start=1)`; `len` can use the stored list."],
        solution="""
        class LineReader:
            def __init__(self, text):
                self._lines = [line.strip() for line in text.splitlines() if line.strip()]

            def __iter__(self):
                yield from self._lines

            def numbered(self):
                return list(enumerate(self, start=1))

            def __len__(self):
                return len(self._lines)
        """,
        why="""Three bugs grew from one decision: storing an **iterator** in `__init__` made the object one-shot. `len()` counted by iterating, which consumed
        every line, so the very first `list(r)` after `len(r)` was empty, a destructive `len` that no caller would expect. `numbered()`
        called `next(self)` to "skip" something, which threw away the first line, and `enumerate` without `start=1` numbered from 0. Storing
        the cleaned list makes iteration repeatable, `len` O(1) and non-destructive, and `numbered` a one-liner. For huge files, where storing
        every line is not an option, the class would keep the **path** and open the file afresh in each `__iter__` (10.2), still re-iterable,
        and `len` would have to be dropped or documented as expensive."""),
    write("A token stream object", "hard", tag="GenAI",
        prompt="""Write an iterator class `TokenStream(deltas)` wrapping an iterable of streamed text pieces. Iterating yields the pieces; meanwhile the
        object exposes `text` (everything received so far), `count` (pieces received) and `finished` (true once the source is exhausted). Add
        `close()`, which stops the stream early (later `next` calls raise `StopIteration`, and `finished` stays false) and closes the source if it
        has a `close` method, and `read_all()` returning the remaining text joined, then the full text.""",
        code="""
        class TokenStream:
            pass
        """,
        tests="""
        closed = []
        def source():
            try:
                for piece in ["Refunds ", "take ", "five ", "days."]:
                    yield piece
            finally:
                closed.append(True)

        s = TokenStream(source())
        assert next(s) == "Refunds " and next(s) == "take " and (s.text, s.count, s.finished) == ("Refunds take ", 2, False)
        assert s.read_all() == "Refunds take five days." and s.finished and s.count == 4
        assert list(s) == [] and closed == [True]

        t = TokenStream(source())
        next(t)
        t.close()
        assert list(t) == [] and not t.finished and t.text == "Refunds " and closed == [True, True]
        assert TokenStream(["a", "b"]).read_all() == "ab"
        """,
        hints=["Keep `self._it = iter(deltas)`, a list of received pieces, and flags. `__next__` raises `StopIteration` if closed or finished.",
               "`read_all` can loop over `self` to consume the rest, then return `self.text`."],
        solution="""
        class TokenStream:
            def __init__(self, deltas):
                self._source = deltas
                self._it = iter(deltas)
                self._pieces = []
                self.finished = False
                self._closed = False

            @property
            def text(self):
                return "".join(self._pieces)

            @property
            def count(self):
                return len(self._pieces)

            def __iter__(self):
                return self

            def __next__(self):
                if self._closed or self.finished:
                    raise StopIteration
                try:
                    piece = next(self._it)
                except StopIteration:
                    self.finished = True
                    raise
                self._pieces.append(piece)
                return piece

            def close(self):
                self._closed = True
                close = getattr(self._it, "close", None)
                if close is not None:
                    close()

            def read_all(self):
                for _ in self:
                    pass
                return self.text
        """,
        why="""A streaming response is consumed incrementally, but other code (a UI, a logger, a token counter) needs to ask **during** the stream how much has
        arrived, and the handler needs to stop it when the user cancels. That combination of iteration plus inspectable state plus extra
        methods is exactly when a hand-written iterator class beats a generator. `finished` is set only when the source itself is exhausted,
        so a closed stream is distinguishable from a completed one, which matters when logging whether an answer was cut short. `close()`
        forwards to the source's `close`, which for a generator runs its `finally` block (6.3), releasing the HTTP connection in a real SDK.
        The OpenAI and Anthropic SDKs return stream objects with this shape (iterable, closable, with accumulated state)."""),
    predict("Iteration fallbacks and reversal", "hard",
        code="""
        class Seq:
            def __init__(self, n):
                self.n = n
            def __getitem__(self, i):
                if i >= self.n:
                    raise IndexError(i)
                return i * 10
            def __len__(self):
                return self.n

        class NotIterable(Seq):
            __iter__ = None

        s = Seq(3)
        print(list(s), 20 in s, list(reversed(s)))
        try:
            iter(NotIterable(3))
        except TypeError as e:
            print("TypeError:", type(e).__name__)

        class OnlyIter:
            def __iter__(self):
                yield from [1, 2, 3]
        try:
            reversed(OnlyIter())
        except TypeError:
            print("reversed needs a sequence")
        print(list(reversed(list(OnlyIter()))))
        """,
        hints=["Without `__iter__`, iteration falls back to `__getitem__` with 0, 1, 2, ... until `IndexError`. `reversed` needs `__reversed__` or `__len__` plus `__getitem__`.",
               "Setting `__iter__ = None` explicitly marks a class as not iterable."],
        why="""`Seq` has no `__iter__`, so `list`, `in` and `for` use the old sequence protocol: calling `__getitem__(0)`, `__getitem__(1)`, ... until
        `IndexError`. `reversed` works because `Seq` has both `__len__` and `__getitem__`. Assigning `__iter__ = None` in a subclass is the
        documented way to block iteration, so `iter()` raises `TypeError` even though `__getitem__` exists. A class with only `__iter__` cannot be
        reversed lazily, because Python cannot know the last item without consuming everything; materialise it into a list first, or implement
        `__reversed__`."""),
)

section("interview", "Interview questions",
    explain("When you design a class that should be iterable, how do you decide between returning `self` from `__iter__` and returning a new iterator?", "medium", tag="Interview",
        why="""Containers (objects that hold or can recompute their items: a collection, a dataset, a range, a result set that can be fetched again) should
        return a **new** iterator from every `__iter__` call, so that several loops, nested loops and repeated epochs each get their own
        position, like lists do; the simplest implementation is a generator method. An object should return **self** only if it is itself a
        one-shot stream whose state is the position: a network stream, a file object, a token stream, a peekable wrapper, a cursor. Such iterators
        must also implement `__next__` and raise `StopIteration` at the end. The classic bug is a container that returns `self` and keeps a
        position attribute: the second loop is silently empty. If re-iteration is expensive (re-fetching pages), document it, or cache the
        results deliberately."""),
    explain("What happens when `StopIteration` is raised inside a generator, and why?", "medium", tag="Interview",
        why="""Since Python 3.7 (PEP 479), if a `StopIteration` propagates out of a generator's body, for example from a bare `next(it)` on an exhausted
        iterator, Python replaces it with `RuntimeError: generator raised StopIteration`. Before that change, the stray `StopIteration` simply
        ended the generator, so a bug in the middle of the generator looked like a normal, shorter stream, and loops consuming it silently lost
        data. The correct ways to end a generator are to fall off the end of its body or to `return` (whose value becomes the
        `StopIteration.value`, used by `yield from`). When pulling from another iterator inside a generator, use `next(it, default)` or catch
        `StopIteration` and `return` explicitly. In hand-written iterator classes, raising `StopIteration` from `__next__` is still the correct
        signal."""),
    explain("How would you expose a large remote result set (a paginated API or a database cursor) as a Python iterable?", "hard", tag="Interview",
        why="""Wrap it in a class whose `__iter__` is a generator that fetches one page (or batch of rows) at a time and yields its items, so memory
        stays bounded, the first results arrive immediately, and the consumer stopping early (a `break`, `islice`) stops the fetching. Use the
        API's cursor or continuation token rather than offsets where possible, since offsets shift when data changes and get slower deep into
        the set. Handle transient errors per page with retries and backoff, respect rate limits between pages, and set timeouts (7.4). Decide
        and document whether the object is re-iterable (each loop re-queries from the start) or a one-shot stream (like a DB cursor); offer a
        `first(n)` helper and avoid `__len__` unless the API reports a total cheaply. Make sure resources are released when iteration stops
        early: closing the generator runs its `finally`, and a context manager (10.2) makes that explicit. Expose counters such as pages
        fetched for observability."""),
)

recap(
    "`for` calls `iter(obj)` then `next(it)` until `StopIteration`; implement `__iter__` (and, for iterators, `__next__` raising `StopIteration`).",
    "Containers return a new iterator from every `__iter__` (usually a generator method); only one-shot streams return `self`.",
    "Prefer a generator `__iter__`; write an iterator class when you need extra methods (`peek`, `close`) or inspectable state.",
    "`iter(func, sentinel)` loops until a sentinel; lazy classes fetch or compute on demand and can offer an arithmetic `__len__`.",
    "Traps: exhausted iterators, `StopIteration` inside generators becomes `RuntimeError` (use `next(it, default)`), and changing collections while iterating.",
)
