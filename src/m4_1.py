from lesson import *

lesson(
    id="m4-1", num="4.1", title="Lists: indexing, slicing and methods",
    intro="How a list is stored and why that makes some operations instant and others slow, the exact rules for indexes "
          "and slices (including the `xs[-0:]` trap), slice assignment, which methods change the list, and when a list "
          "is the wrong tool.",
    desc="Negative indexes, slice rules, `append` vs `extend`, `insert`, `pop`, `remove`.",
    keys="list dynamic array index negative index slice step slice assignment del append extend insert pop remove clear reverse index count deque maxlen window amortized",
)

term("Dynamic array", "How CPython stores a list: one block of memory holding references to the items, with spare room at the end so appends are cheap.")
term("Slice", "`xs[start:stop:step]`: a new list with the items from `start` up to, but not including, `stop`, taking every `step`-th item.")
term("Slice assignment", "`xs[a:b] = items` replaces that part of the list in place; the list can grow or shrink.")
term("Amortized O(1)", "An operation that is occasionally slow (a resize) but cheap on average over many calls, like `list.append`.")
term("deque", "`collections.deque`: a double-ended queue with fast adds and removes at both ends, and an optional `maxlen` that drops old items.")

ARRAY_FIG = """
<svg viewBox="0 0 640 120" role="img" aria-label="A list object holds a length, a capacity and a pointer to an array of references. Each slot points at an object stored elsewhere.">
  <defs><marker id="l1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="10" y="20" width="130" height="64" rx="12" class="box a"/>
  <text x="75" y="44" class="w mid">list object</text><text x="75" y="64" class="w mid">len 3, room for 4</text>
  <rect x="170" y="34" width="60" height="36" rx="6" class="box"/><text x="200" y="57" class="tk">[0]</text>
  <rect x="230" y="34" width="60" height="36" rx="6" class="box"/><text x="260" y="57" class="tk">[1]</text>
  <rect x="290" y="34" width="60" height="36" rx="6" class="box"/><text x="320" y="57" class="tk">[2]</text>
  <rect x="350" y="34" width="60" height="36" rx="6" class="box" style="stroke-dasharray:4 3"/><text x="380" y="57" class="mid">spare</text>
  <rect x="440" y="10" width="90" height="26" rx="8" class="box b"/><text x="485" y="28" class="w mid">"rag"</text>
  <rect x="440" y="44" width="90" height="26" rx="8" class="box b"/><text x="485" y="62" class="w mid">0.92</text>
  <rect x="440" y="78" width="90" height="26" rx="8" class="box b"/><text x="485" y="96" class="w mid">{...}</text>
  <path d="M140 52 L166 52" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#l1)"/>
  <path d="M200 70 C 250 110, 400 30, 436 24" style="stroke:var(--label2);stroke-width:1.5;fill:none" marker-end="url(#l1)"/>
  <path d="M260 70 C 300 100, 400 60, 436 57" style="stroke:var(--label2);stroke-width:1.5;fill:none" marker-end="url(#l1)"/>
  <path d="M320 70 C 360 100, 410 95, 436 91" style="stroke:var(--label2);stroke-width:1.5;fill:none" marker-end="url(#l1)"/>
</svg>"""

section("model", "What a list is in memory",
    p("""In CPython, a list is a **dynamic array of references**: the list object stores its length, how much room it has,
    and a pointer to one contiguous block of slots. Each slot holds a **reference** to an item stored somewhere else
    (2.1), which is why one list can hold a string, a float and a dict side by side, and why copying a list copies the
    references, not the items (2.3)."""),
    fig(ARRAY_FIG, "A list is a block of slots, each pointing at an object. The block has spare room at the end."),
    p("""Every performance rule of lists follows from that picture:"""),
    p("""- **`xs[i]` is O(1).** The slot's address is "start + i times slot size", one calculation whatever the length.
    - **`append` is amortized O(1).** There is usually spare room at the end, so appending just fills the next slot. When
      the room runs out, Python allocates a bigger block (with extra room to spare) and moves the references over. That
      resize is O(n), but it happens rarely enough that the average cost per append stays constant.
    - **`insert(0, x)` and `pop(0)` are O(n).** Every other reference has to shift one slot to make or close the gap.
    - **`x in xs`, `xs.index(x)`, `xs.remove(x)` are O(n).** Nothing tells Python where a value is, so it checks slots one
      by one (2.1: identity first, then equality)."""),
    ex("""
    import sys

    xs = []
    sizes = []
    for i in range(12):
        xs.append(i)
        sizes.append(sys.getsizeof(xs))
    print(sizes)                    # the size only jumps now and then: spare room in action
    print(len(xs), xs[7], xs[-1])
    """, "growth.py"),
    p("""The exact byte numbers depend on the Python version and platform, so do not memorise them. What matters is the
    pattern: the size stays flat for several appends, then jumps. Each jump is one resize, and between jumps an append
    only fills a spare slot."""),
)

section("indexing", "Indexing, step by step",
    p("""Valid indexes for a list of length `n` run from `0` to `n - 1`. A **negative** index counts from the end: Python
    converts `xs[-k]` to `xs[n - k]`, so `-1` is the last item and `-n` the first. Anything outside `-n .. n - 1` raises
    `IndexError`."""),
    html("""<div class="tbl"><table>
      <tr><th>item</th><td><code>"sys"</code></td><td><code>"user"</code></td><td><code>"asst"</code></td><td><code>"user"</code></td><td><code>"asst"</code></td></tr>
      <tr><th>positive index</th><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
      <tr><th>negative index</th><td>-5</td><td>-4</td><td>-3</td><td>-2</td><td>-1</td></tr>
    </table></div>"""),
    ex("""
    roles = ["sys", "user", "asst", "user", "asst"]
    print(roles[0], roles[-1], roles[-2], roles[len(roles) - 1])
    try:
        roles[5]
    except IndexError as e:
        print("IndexError:", e)
    print(roles.index("user"), roles.count("asst"))   # first position of a value, and how many
    """, "indexing.py"),
    callout("sql", "SQL / Power BI", """Unlike SQL rows, list items have a guaranteed order and a position. `roles[-1]` is
    "the last row" without an `ORDER BY ... DESC` and `TOP 1`. But a list index is only meaningful while the list does
    not change: delete one item and every later index shifts, which is the source of the classic delete-while-looping bug
    (problem 6).""")
)

section("slicing", "Slicing rules",
    p("""`xs[start:stop:step]` builds a **new list** (a shallow copy, 2.3) with the items from `start` **up to but not
    including** `stop`, taking every `step`-th one. Each part is optional, and the rules for filling them in are what you
    need to predict any slice:"""),
    p("""- With a positive `step` (default 1): a missing `start` means 0, a missing `stop` means "to the end".
    - With a negative `step`: the slice walks **backwards**, a missing `start` means "the last item" and a missing `stop`
      means "past the beginning". `xs[::-1]` is a reversed copy.
    - Negative `start` and `stop` count from the end, exactly like indexes.
    - Out-of-range bounds are **clamped**, never an error: `xs[2:100]` on a 5-item list gives the last three items, and
      `xs[10:20]` gives `[]`.
    - If `start` is already at or past `stop` in the direction of travel, the slice is empty."""),
    ex("""
    t = ["a", "b", "c", "d", "e", "f"]
    print(t[1:4], t[:2], t[4:], t[-2:])
    print(t[::2], t[1::2], t[::-1], t[4:1:-1])
    print(t[2:100], t[10:20], t[4:2])
    """, "slicing.py"),
    p("""**The `-0` trap.** "The last `n` items" is usually written `xs[-n:]`. It works for every `n` from 1 up, but for
    `n = 0` the start is `-0`, which is just `0`, so `xs[-0:]` is `xs[0:]`: the **whole list**, the opposite of what you
    meant. Code that trims chat history or keeps "the last k scores" hits this whenever `k` can be 0. Write
    `xs[len(xs) - n:]` or guard `n == 0` explicitly."""),
    ex("""
    history = ["m1", "m2", "m3", "m4"]
    for n in [2, 1, 0]:
        print(n, history[-n:], history[len(history) - n:])
    """, "minus_zero.py"),
)

section("assign", "Slice assignment and `del`",
    p("""On the left of `=`, a slice means "replace this part of the list **in place**". The right side can be any iterable,
    and the list grows or shrinks to fit, so slice assignment can insert, replace or delete. `del xs[a:b]` removes a range
    in place. With a step other than 1 ("extended slices"), the right side must have exactly as many items as the slice
    selects."""),
    ex("""
    xs = [0, 1, 2, 3, 4]
    xs[1:3] = ["a", "b", "c"]      # replace two items with three: the list grows
    print(xs)
    xs[:0] = ["start"]             # an empty slice at the front: insert
    print(xs)
    del xs[-2:]                    # remove the last two
    print(xs)
    xs[::2] = [None] * len(xs[::2])  # extended slice: lengths must match
    print(xs)
    try:
        xs[::2] = [1]
    except ValueError as e:
        print("ValueError:", e)
    """, "slice_assignment.py"),
    p("""`xs[:] = new_items` replaces the whole contents while keeping the **same list object**, which is how you change a
    list in place for every alias (2.2, `normalise_inplace`). By contrast, `xs = xs[2:]` builds a new list and moves only
    the local name: callers holding the old list see no change (problem 14)."""),
)

section("methods", "Methods: which change the list, and what they cost",
    html("""<div class="tbl"><table>
      <tr><th>Method</th><th>Changes the list?</th><th>Returns</th><th>Cost</th></tr>
      <tr><td><code>append(x)</code></td><td>yes</td><td><code>None</code></td><td>O(1) amortized</td></tr>
      <tr><td><code>extend(iterable)</code>, <code>+=</code></td><td>yes</td><td><code>None</code></td><td>O(k) for k new items</td></tr>
      <tr><td><code>insert(i, x)</code></td><td>yes</td><td><code>None</code></td><td>O(n): shifts everything after i</td></tr>
      <tr><td><code>pop()</code> / <code>pop(i)</code></td><td>yes</td><td>the removed item</td><td>O(1) at the end, O(n) elsewhere</td></tr>
      <tr><td><code>remove(x)</code></td><td>yes</td><td><code>None</code></td><td>O(n): search, then shift</td></tr>
      <tr><td><code>sort()</code>, <code>reverse()</code>, <code>clear()</code></td><td>yes</td><td><code>None</code></td><td>O(n log n), O(n), O(n)</td></tr>
      <tr><td><code>index(x)</code>, <code>count(x)</code>, <code>x in xs</code></td><td>no</td><td>a position, a count, a bool</td><td>O(n)</td></tr>
      <tr><td><code>xs + ys</code>, <code>xs * k</code>, slicing, <code>sorted(xs)</code></td><td>no</td><td>a new list</td><td>O(size of result)</td></tr>
    </table></div>"""),
    p("""The most common mix-up is `append` versus `extend`. `append(x)` adds **one item**, whatever `x` is, so appending a
    list nests it. `extend(iterable)` adds **each item** of the iterable, so extending with a string adds its characters
    one by one. When you collect chunks from several documents, you almost always mean `extend` (problem 2)."""),
    ex("""
    chunks = []
    chunks.append(["c1", "c2"])        # one item: a nested list
    chunks.extend(["c3", "c4"])        # two items
    chunks.extend("ab")                # a string is an iterable of characters
    print(chunks, len(chunks))
    last = chunks.pop()
    print(last, chunks.pop(0), chunks)
    """, "append_extend.py"),
    callout("note", "When a list is the wrong tool", """Use `collections.deque` when you add or remove at the **front**
    (a queue, a breadth-first search) or need a fixed-size **window** (`deque(maxlen=20)` keeps the last 20 chat turns and
    drops older ones automatically). Use a `set` or `dict` when you mostly ask "is `x` in here?" (4.4, 4.5). Use a numpy
    array for large numeric data, where whole-array operations run in C (2.2)."""),
)

section("warmup", "Warm-up",
    predict("Indexes and slices on chat roles", "easy",
        code="""
        tokens = ["<s>", "how", "do", "refunds", "work", "?", "</s>"]
        print(tokens[-1], tokens[-2], tokens[1])
        print(tokens[1:-1])
        print(tokens[-3:], tokens[::3])
        print(tokens[5:10], tokens[4:2], tokens[::-1][:2])
        """,
        hints=["`stop` is never included; out-of-range bounds are clamped; a reversed copy starts from the end."],
        why="""`tokens[1:-1]` drops the first and the last item, a common way to strip start and end markers. `[-3:]` is the last
        three, and `[::3]` takes positions 0, 3 and 6. `tokens[5:10]` is clamped to positions 5 and 6. `tokens[4:2]` is empty
        because 4 is already past 2 going forwards. `tokens[::-1][:2]` reverses first, then takes two."""),
    fix("Chunks collected as nested lists", "easy", tag="RAG",
        prompt="""`collect_chunks(docs, chunker)` should return one flat list of chunks from all documents. It returns a list of
        lists, which breaks the embedding step that expects strings. Fix it.""",
        code="""
        def collect_chunks(docs, chunker):
            all_chunks = []
            for doc in docs:
                all_chunks.append(chunker(doc))
            return all_chunks
        """,
        tests="""
        split = lambda d: d.split(". ")
        out = collect_chunks(["A. B", "C"], split)
        assert out == ["A", "B", "C"]
        assert all(isinstance(c, str) for c in out)
        assert collect_chunks([], split) == []
        """,
        hints=["`append` adds one item. Which method adds each item of a list?"],
        solution="""
        def collect_chunks(docs, chunker):
            all_chunks = []
            for doc in docs:
                all_chunks.extend(chunker(doc))
            return all_chunks
        """,
        why="""`chunker(doc)` returns a list, and `append` adds that list as **one** item. `extend` adds each chunk separately.
        A flat comprehension, `[c for doc in docs for c in chunker(doc)]`, does the same in one expression (lesson 6.2). This bug
        is easy to miss because `len(all_chunks)` looks plausible: it equals the number of documents instead of the number of
        chunks."""),
    write("The last n turns, safely", "easy", tag="GenAI",
        prompt="""Write `last_turns(history, n)` that returns a new list with the system message (if `history[0]["role"] ==
        "system"`) followed by the last `n` **other** messages. `n = 0` must give just the system message (or `[]`). Watch out
        for the `-0` trap.""",
        code="""
        def last_turns(history, n):
            pass
        """,
        tests="""
        h = [{"role": "system", "content": "S"}, {"role": "user", "content": "1"}, {"role": "assistant", "content": "2"},
             {"role": "user", "content": "3"}]
        assert [m["content"] for m in last_turns(h, 2)] == ["S", "2", "3"]
        assert [m["content"] for m in last_turns(h, 0)] == ["S"]
        assert [m["content"] for m in last_turns(h, 10)] == ["S", "1", "2", "3"]
        assert last_turns(h[1:], 1) == [{"role": "user", "content": "3"}]
        assert last_turns([], 3) == []
        """,
        hints=["Split off the system message first: `head = history[:1]` if it is a system message, `rest` is everything else.",
               "`rest[len(rest) - n:]` is safe for `n = 0`, but what if `n > len(rest)`? A negative start is counted from the end, so use `max(0, ...)`."],
        solution="""
        def last_turns(history, n):
            has_system = bool(history) and history[0]["role"] == "system"
            head = history[:1] if has_system else []
            rest = history[1:] if has_system else history
            return head + rest[max(0, len(rest) - n):]
        """,
        why="""`rest[-n:]` would return everything for `n = 0`, exactly the opposite of "no turns". Computing the start as
        `len(rest) - n` avoids that, and `max(0, ...)` stops a large `n` from producing a negative start, which would count from
        the end instead of meaning "from the beginning". Slicing (`history[:1]`, `history[1:]`) also handles the empty list
        without special cases, because slices never raise. Building the result with `+` returns a new list and leaves the
        caller's history alone (2.4)."""),
    predict("Methods that return None", "easy",
        code="""
        x = [3, 1, 2]
        y = x.sort()
        z = sorted(x, reverse=True)
        x.append(x.pop(0))
        print(x, y, z)
        w = x.reverse()
        print(x, w, x.index(3), x.count(9))
        """,
        hints=["`sort`, `append` and `reverse` change the list and return `None`; `pop` returns the item it removed."],
        why="""`x.sort()` sorts `x` to `[1, 2, 3]` and returns `None`, so `y` is `None`. `sorted` returns a new list. `x.pop(0)`
        removes and returns `1`, and `append` puts it at the end: `[2, 3, 1]`. `reverse()` reverses in place to `[1, 3, 2]` and
        returns `None`. `index(3)` finds position 1, and `count(9)` is 0 rather than an error."""),
)

section("medium", "Medium",
    write("Sliding windows over a series", "medium", tag="ML",
        prompt="""Write `windows(xs, size, step=1)` that returns the list of slices `xs[i:i + size]` for every start `i` that
        gives a **full** window, moving `step` positions each time. Used to build training examples from a time series.
        Raise `ValueError` if `size` or `step` is less than 1.""",
        code="""
        def windows(xs, size, step=1):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        s = [1, 2, 3, 4, 5]
        assert windows(s, 3) == [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
        assert windows(s, 2, 2) == [[1, 2], [3, 4]]
        assert windows(s, 6) == []
        assert windows(s, 5) == [[1, 2, 3, 4, 5]]
        assert raises(ValueError, windows, s, 0) and raises(ValueError, windows, s, 2, 0)
        """,
        hints=["The last full window starts at `len(xs) - size`, so the starts are `range(0, len(xs) - size + 1, step)`."],
        solution="""
        def windows(xs, size, step=1):
            if size < 1 or step < 1:
                raise ValueError("size and step must be at least 1")
            return [xs[i:i + size] for i in range(0, len(xs) - size + 1, step)]
        """,
        why="""The range of starts does the "full windows only" work: if `size > len(xs)`, the stop of the range is 0 or negative,
        so it is empty and no window is produced, without any special case. Each window is a new list (a slice), so changing
        one cannot affect the series or the other windows. With numpy, `np.lib.stride_tricks.sliding_window_view` produces the
        same windows as **views** without copying, which is much faster for long series but shares memory (2.2)."""),
    fix("Deleting by position shifts the rest", "medium", tag="Data work",
        prompt="""`drop_rows(rows, bad_positions)` should remove the rows at the given positions, in place. It removes the
        wrong rows and sometimes crashes. Fix it, keeping it in place (the same list object).""",
        code="""
        def drop_rows(rows, bad_positions):
            for i in bad_positions:
                del rows[i]
        """,
        tests="""
        rows = ["r0", "r1", "r2", "r3", "r4"]
        ref = rows
        drop_rows(rows, [1, 3])
        assert rows == ["r0", "r2", "r4"] and rows is ref
        data = list("abcde")
        drop_rows(data, [4, 0])
        assert data == ["b", "c", "d"]
        drop_rows(data, [])
        assert data == ["b", "c", "d"]
        """,
        hints=["After `del rows[1]`, which row is now at position 3?",
               "Delete from the highest position down, or rebuild the contents with slice assignment."],
        solution="""
        def drop_rows(rows, bad_positions):
            bad = set(bad_positions)
            rows[:] = [r for i, r in enumerate(rows) if i not in bad]
        """,
        why="""Each `del` shifts every later row one position to the left, so the next position points at a different row than
        intended, and a position near the end can be past the new end (`IndexError`). Two correct fixes: delete in **descending**
        order (`for i in sorted(bad_positions, reverse=True)`), so earlier positions are not affected, or rebuild the contents in
        one pass with slice assignment, which is O(n) overall instead of O(n) per deletion. The set makes each membership check
        O(1) (4.4)."""),
    trace("Slice assignment, step by step", "medium",
        prompt="Fill in `xs` and `len(xs)` after each marked line.",
        code="""
        xs = [0, 1, 2, 3, 4]
        xs[1:3] = ["a"]  # row: "xs[1:3] = ['a']"
        xs[:0] = [9, 9]  # row: "xs[:0] = [9, 9]"
        del xs[::2]  # row: "del xs[::2]"
        xs[len(xs):] = [7]  # row: "xs[len(xs):] = [7]"
        """,
        trace_vars=["xs", "len(xs)"],
        hints=["Slice assignment replaces exactly the selected part, whatever the lengths. `del xs[::2]` removes every other item, starting at position 0."],
        why="""`xs[1:3] = ["a"]` replaces two items with one, so the list shrinks to `[0, "a", 3, 4]`. `xs[:0] = ...` replaces an
        empty slice at the front, which inserts. `del xs[::2]` deletes positions 0, 2 and 4 of `[9, 9, 0, "a", 3, 4]`, leaving
        `[9, "a", 4]`. `xs[len(xs):] = [7]` replaces the empty slice at the end, which is the same as `extend`. Every one of
        these changes the same list object in place."""),
    choose("A queue built on a list", "medium",
        prompt="Both process 50,000 queued jobs in arrival order. Which is faster?",
        setup="""from collections import deque
jobs = list(range(50_000))""",
        options={
            "a": "q = list(jobs)\nwhile q:\n    job = q.pop(0)",
            "b": "q = deque(jobs)\nwhile q:\n    job = q.popleft()",
        },
        answer="b",
        hints=["What does `pop(0)` have to do with every remaining item?"],
        why="""`list.pop(0)` removes the first slot and shifts every remaining reference one place left: O(n) per pop, O(n²) for
        the whole queue. A `deque` is built for both ends, so `popleft()` is O(1). Breadth-first search, job queues and
        streaming windows all want a deque. `list.pop()` from the **end** is O(1), so a list is fine as a stack."""),
    write("Keep the newest messages within a token budget", "medium", tag="GenAI",
        prompt="""Write `fit_budget(messages, budget, count=len)` that returns a new list containing the system message (if
        the first message has role `"system"`, always kept) plus as many of the **newest** other messages as fit, so that the
        total `count(m["content"])` of everything kept is at most `budget`. Keep chronological order. Stop at the first message
        that does not fit (do not skip ahead to older, smaller ones).""",
        code="""
        def fit_budget(messages, budget, count=len):
            pass
        """,
        tests="""
        msgs = [{"role": "system", "content": "abc"}, {"role": "user", "content": "aaaaaa"},
                {"role": "assistant", "content": "bb"}, {"role": "user", "content": "cccc"}]
        assert [m["content"] for m in fit_budget(msgs, 9)] == ["abc", "bb", "cccc"]
        assert [m["content"] for m in fit_budget(msgs, 7)] == ["abc", "cccc"]
        assert [m["content"] for m in fit_budget(msgs, 3)] == ["abc"]
        assert [m["content"] for m in fit_budget(msgs[1:], 6)] == ["bb", "cccc"]
        words = lambda text: len(text.split())
        assert len(fit_budget(msgs, 100, count=words)) == 4
        """,
        hints=["Walk the non-system messages from newest to oldest (`reversed(rest)`), adding while the total stays within the budget.",
               "You collected newest first; reverse once at the end, or insert into a deque on the left."],
        solution="""
        def fit_budget(messages, budget, count=len):
            has_system = bool(messages) and messages[0]["role"] == "system"
            head = messages[:1] if has_system else []
            rest = messages[1:] if has_system else messages
            used = sum(count(m["content"]) for m in head)
            kept = []
            for m in reversed(rest):
                cost = count(m["content"])
                if used + cost > budget:
                    break
                kept.append(m)
                used += cost
            kept.reverse()
            return head + kept
        """,
        why="""Walking backwards with `reversed(rest)` (a lazy iterator, no copy) visits the newest messages first, and `break`
        stops at the first one that does not fit, so the kept turns are always a contiguous recent window: skipping ahead to an
        older small message would put a reply in context without the question it answers. Appending then reversing once is O(n);
        inserting at position 0 for each message would be O(n²). `count` is a parameter (3.5), so the same function works with a
        real tokenizer, such as `lambda t: len(enc.encode(t))` with tiktoken."""),
    refactor("Index loops to slices", "medium",
        prompt="Rewrite with slicing, `reversed` and `enumerate` instead of manual indexes. Same results. Keep the tests green.",
        code="""
        def summary(scores):
            top3 = []
            i = 0
            while i < 3 and i < len(scores):
                top3.append(scores[i])
                i += 1
            backwards = []
            for j in range(len(scores) - 1, -1, -1):
                backwards.append(scores[j])
            evens = []
            for k in range(len(scores)):
                if k % 2 == 0:
                    evens.append(scores[k])
            return top3, backwards, evens
        """,
        tests="""
        assert summary([5, 4, 3, 2, 1]) == ([5, 4, 3], [1, 2, 3, 4, 5], [5, 3, 1])
        assert summary([7]) == ([7], [7], [7])
        assert summary([]) == ([], [], [])
        """,
        hints=["Three slices: the first three, a reversed copy, and every second item from position 0."],
        solution="""
        def summary(scores):
            return scores[:3], scores[::-1], scores[::2]
        """,
        why="""Each loop re-implemented a slice by hand, including its clamping (`i < len(scores)`) and its step. Slices express
        the intent directly, clamp automatically (so the empty and short lists need no special handling), run in C, and return
        new lists, exactly like the loops did. When you see `range(len(xs) - 1, -1, -1)`, think `xs[::-1]` or `reversed(xs)`."""),
    predict("List slice versus numpy slice", "medium", tag="ML",
        code="""
        import numpy as np

        lst = [10, 20, 30, 40]
        arr = np.array(lst)
        ls = lst[1:3]
        sl = arr[1:3]
        ls[0] = -1
        sl[0] = -1
        print(lst, ls)
        print(arr, sl)
        print(lst[::-1] is lst, np.shares_memory(arr[::-1], arr))
        """,
        hints=["A list slice is a new list. A numpy basic slice is a view (2.2)."],
        why="""Changing the list slice does not touch `lst`, because a list slice is a new list holding copies of the
        references. The numpy slice is a **view** of the same memory, so `sl[0] = -1` writes into `arr`. Even a reversed numpy
        slice is a view (it just walks the memory backwards), while a reversed list slice is always a new list. Code that moves
        between lists and arrays has to keep both rules in mind."""),
    write("Batch boundaries for an embedding job", "medium", tag="ML",
        prompt="""Write `batch_bounds(n, batch_size)` that returns a list of `(start, stop)` pairs covering positions `0` to
        `n`, each batch `batch_size` long except possibly the last. These are used as `items[start:stop]`.""",
        code="""
        def batch_bounds(n, batch_size):
            pass
        """,
        tests="""
        assert batch_bounds(10, 4) == [(0, 4), (4, 8), (8, 10)]
        assert batch_bounds(8, 4) == [(0, 4), (4, 8)]
        assert batch_bounds(0, 4) == []
        assert batch_bounds(3, 10) == [(0, 3)]
        items = list("abcdefghij")
        assert [items[a:b] for a, b in batch_bounds(len(items), 4)][-1] == ["i", "j"]
        """,
        hints=["Starts are `range(0, n, batch_size)`; the stop is `min(start + batch_size, n)`."],
        solution="""
        def batch_bounds(n, batch_size):
            return [(start, min(start + batch_size, n)) for start in range(0, n, batch_size)]
        """,
        why="""Returning bounds instead of the batches themselves avoids copying the data and lets the same bounds index several
        aligned lists (texts, ids, metadata) in step. `min(..., n)` makes the last pair exact, although slicing would clamp
        `items[8:12]` anyway; exact bounds matter when they are logged or used for numpy arrays and progress bars. The count of
        batches is the ceiling division from 1.P: `-(-n // batch_size)`."""),
)

section("hard", "Hard",
    predict("Slice edge cases", "hard",
        code="""
        xs = [1, 2, 3, 4, 5]
        print(xs[-0:], xs[len(xs):], xs[-100:2])
        print(xs[10:-10:-1], xs[3:0:-2], xs[::-2])
        s = slice(1, None, 2)
        print(xs[s], s.indices(len(xs)))
        print(xs[::-1][::-1] == xs, xs[::-1][::-1] is xs)
        """,
        hints=["`-0` is `0`. With a negative step, bounds beyond the ends are clamped to the ends in the walking direction.",
               "`slice.indices(n)` shows the actual `(start, stop, step)` Python uses for a sequence of length `n`."],
        why="""`xs[-0:]` is the whole list (the trap), `xs[len(xs):]` is empty, and `xs[-100:2]` clamps the start to 0. With a
        negative step, `10` clamps to the last item and `-10` to "before the first", so `xs[10:-10:-1]` is the whole list
        reversed; `xs[3:0:-2]` walks from position 3 down to (not including) 0 by twos. A `slice` object is just the three
        numbers, reusable and nameable (`HEADER = slice(0, 3)`), and `.indices` shows how Python normalises it. Reversing twice
        gives an equal list, but a new one each time."""),
    fix("Read the code: a context window that never shrinks", "hard", tag="GenAI",
        prompt="""This module keeps a rolling window of recent messages for each chat. The caller's window keeps growing past
        `max_turns`, and asking for the `0` most recent messages returns everything. Read the module, find both bugs and fix
        them. `add` must change the caller's list in place.""",
        code="""
        def add(window, message, max_turns):
            \"\"\"Append a message, then drop the oldest so at most max_turns remain.\"\"\"
            window.append(message)
            if len(window) > max_turns:
                window = window[-max_turns:]
            return None


        def recent(window, n):
            \"\"\"The n most recent messages, oldest first.\"\"\"
            return window[-n:]


        def as_prompt(window, n):
            return "\\n".join(f"{m['role']}: {m['content']}" for m in recent(window, n))
        """,
        tests="""
        w = []
        for i in range(5):
            add(w, {"role": "user", "content": f"m{i}"}, max_turns=3)
        assert [m["content"] for m in w] == ["m2", "m3", "m4"]
        assert [m["content"] for m in recent(w, 2)] == ["m3", "m4"]
        assert recent(w, 0) == []
        assert as_prompt(w, 1) == "user: m4"
        assert recent(w, 10) == w
        """,
        hints=["`window = window[-max_turns:]` builds a new list and moves the **local** name. What does the caller still hold?",
               "Delete the oldest items in place with `del window[:len(window) - max_turns]`.",
               "For `recent`, avoid the `-0` start the same way as problem 3."],
        solution="""
        def add(window, message, max_turns):
            \"\"\"Append a message, then drop the oldest so at most max_turns remain.\"\"\"
            window.append(message)
            if len(window) > max_turns:
                del window[:len(window) - max_turns]
            return None


        def recent(window, n):
            \"\"\"The n most recent messages, oldest first.\"\"\"
            return window[max(0, len(window) - n):]


        def as_prompt(window, n):
            return "\\n".join(f"{m['role']}: {m['content']}" for m in recent(window, n))
        """,
        why="""Bug one is rebinding instead of changing (2.2, 2.4): `window = window[-max_turns:]` makes a trimmed **copy** and
        points the local name at it, while the caller's list keeps every message. `del window[:k]` removes the oldest `k`
        items from the caller's own list. Bug two is the `-0` trap: `window[-0:]` is the whole window. In production you would
        use `collections.deque(maxlen=max_turns)`, which drops the oldest item automatically on each append, in O(1)."""),
    write("Rotate a list in place", "hard", tag="Interview",
        prompt="""Write `rotate(xs, k)` that rotates `xs` **to the right** by `k` positions **in place** (the same list
        object) and returns `None`. `k` may be larger than the length or negative (negative rotates left). An empty list stays
        empty.""",
        code="""
        def rotate(xs, k):
            pass
        """,
        tests="""
        a = [1, 2, 3, 4, 5]
        ref = a
        assert rotate(a, 2) is None
        assert a == [4, 5, 1, 2, 3] and a is ref
        b = [1, 2, 3]
        rotate(b, 7)
        assert b == [3, 1, 2]
        c = [1, 2, 3, 4]
        rotate(c, -1)
        assert c == [2, 3, 4, 1]
        e = []
        rotate(e, 3)
        assert e == []
        """,
        hints=["Rotating by `k` and by `k % len(xs)` give the same result, and Python's `%` already turns a negative `k` into the right positive amount (1.1).",
               "The rotated list is `xs[-k:] + xs[:-k]`. Put it back with slice assignment, and beware `k == 0` (the `-0` trap again)."],
        solution="""
        def rotate(xs, k):
            if not xs:
                return None
            k %= len(xs)
            xs[:] = xs[len(xs) - k:] + xs[:len(xs) - k]
        """,
        why="""`k % len(xs)` reduces any rotation to `0 .. n - 1`, and because Python's modulo takes the sign of the divisor,
        `-1 % 4` is 3: rotating left by one is rotating right by three. Using `len(xs) - k` as the split point instead of `-k`
        avoids the `-0` trap when `k` becomes 0. Slice assignment keeps the same list object. This uses O(n) extra memory for the
        temporary slices; the classic interview follow-up is the O(1)-memory version, which reverses the whole list and then
        reverses each part. `collections.deque.rotate(k)` does it for deques."""),
    write("Merge two sorted lists", "hard", tag="Interview",
        prompt="""Write `merge_sorted(a, b)` that returns one sorted list from two already-sorted lists in O(len(a) + len(b))
        time, **without** calling `sort` or `sorted`. Equal items from `a` come before those from `b`. Used to combine ranked
        results from two retrievers that are already in score order.""",
        code="""
        def merge_sorted(a, b):
            pass
        """,
        tests="""
        assert merge_sorted([1, 4, 9], [2, 3, 10, 11]) == [1, 2, 3, 4, 9, 10, 11]
        assert merge_sorted([], [1, 2]) == [1, 2] and merge_sorted([3], []) == [3]
        left = [(1, "a"), (2, "a")]
        right = [(1, "b")]
        assert merge_sorted([x[0] for x in left], [x[0] for x in right]) == [1, 1, 2]
        big = merge_sorted(list(range(0, 2000, 2)), list(range(1, 2000, 2)))
        assert big == list(range(2000))
        """,
        hints=["Two positions `i` and `j`. While both lists have items left, append the smaller current item and advance that position.",
               "When one list runs out, the rest of the other is already sorted: add it with a slice and `extend`."],
        solution="""
        def merge_sorted(a, b):
            out = []
            i = j = 0
            while i < len(a) and j < len(b):
                if b[j] < a[i]:
                    out.append(b[j])
                    j += 1
                else:
                    out.append(a[i])
                    i += 1
            out.extend(a[i:])
            out.extend(b[j:])
            return out
        """,
        why="""Each comparison moves one position forward, so the loop runs at most `len(a) + len(b)` times: O(n + m), better
        than concatenating and sorting (O((n + m) log(n + m))). Taking from `a` unless `b`'s item is **strictly** smaller keeps the
        merge stable: equal items from `a` come first. Extending with the two leftover slices handles the tail in one step,
        since only one of them is non-empty. This "two pointers" pattern is the merge step of merge sort, `heapq.merge` does it
        lazily for many lists, and it is how hybrid search combines ranked lists before rank fusion (Module 16)."""),
)

section("interview", "Interview questions",
    explain("Why is `list.append` O(1) but `list.insert(0, x)` O(n)?", "medium", tag="Interview",
        why="""A CPython list is a dynamic array of references with spare capacity at the end. `append` writes into the next
        free slot, which is O(1); when the capacity runs out, the list allocates a larger block (growing by a fraction of its
        size) and copies the references, which is O(n) but rare enough that the cost averages out to O(1) per append
        (amortized). `insert(0, x)` must shift every existing reference one slot to the right to open the gap, so it is O(n)
        every time, and `pop(0)` shifts them back. For fast operations at both ends, use `collections.deque`. Follow-ups worth
        mentioning: indexing is O(1) because slots are contiguous, and `x in list` is O(n) because there is no index of values."""),
    explain("Why does `xs[-n:]` break for `n = 0`, and how do you write \"the last n items\" safely?", "medium", tag="Interview",
        why="""Because `-0` equals `0`, so `xs[-0:]` means `xs[0:]`, the whole list, while "the last 0 items" should be empty.
        It only fails for exactly that value, so it slips through tests that use `n >= 1`. Safe forms: `xs[len(xs) - n:]` (with
        `max(0, ...)` if `n` can exceed the length), or `xs[-n:] if n else []`, or for a rolling window a `deque(maxlen=n)`.
        Mention where it bites in practice: trimming chat history, "keep the last k checkpoints", or taking the last k scores
        for early stopping."""),
    explain("When do you use a Python list, and when a numpy array, for numeric data?", "hard", tag="Interview",
        why="""A list stores references to separate Python objects, can mix types, grows cheaply with `append`, and is ideal for
        building up results, small data, or heterogeneous records. A numpy array stores raw numbers of one dtype in one block, so
        it uses far less memory and runs whole-array operations (`arr * 2`, `arr.mean()`, matrix products) in compiled code,
        often 10 to 100 times faster than Python loops. But arrays have a fixed size (appending copies the whole array), and basic
        slices are **views** that share memory, while list slices are copies. A common pattern: collect in a list, then convert
        once with `np.array(values)`. Mention that object-dtype arrays lose most of the benefit, and that pandas is built on the
        same array model."""),
)

recap(
    "A list is a dynamic array of references: indexing and `append` are O(1); `insert(0)`, `pop(0)`, `in`, `remove` and `index` are O(n).",
    "Negative indexes count from the end. Slices never raise: they clamp. `stop` is never included.",
    "`xs[-n:]` is the whole list when `n == 0`. Use `xs[len(xs) - n:]` or guard zero.",
    "Slice assignment and `del` change the list in place and can grow or shrink it. `xs = xs[...]` only moves your local name.",
    "`append` adds one item; `extend` adds each item. Use `deque` for queues and windows, sets and dicts for membership, numpy for big numbers.",
)
