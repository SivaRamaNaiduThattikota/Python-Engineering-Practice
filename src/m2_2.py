from lesson import *

lesson(
    id="m2-2", num="2.2", title="Mutable and immutable objects, and aliasing",
    intro="Some objects can change in place, some never can. When two names point at one object that can change, "
          "a change through one name shows up everywhere. This lesson is about seeing that coming, in plain Python, "
          "in numpy and in pandas 3.",
    desc="Which types can change in place, and what happens when two names share one object.",
    keys="mutable immutable alias aliasing in place append extend += sort sorted none return tuple list dict fromkeys numpy view pandas copy on write settingwithcopywarning chained assignment",
)

term("Mutable", "An object that can be changed in place after it is created: list, dict, set, most class instances, numpy arrays, DataFrames.")
term("Immutable", "An object that can never change after it is created: int, float, bool, str, tuple, frozenset, bytes, None.")
term("Aliasing", "Two or more names (or container slots) pointing at the same object. Changes through one are visible through all.")
term("In-place", "An operation that changes the existing object instead of building a new one, such as `list.sort()` or `+=` on a list.")
term("View", "A numpy array that looks at another array's memory. Changing the view changes the original.")
term("Copy-on-Write", "pandas 3 behaviour: anything taken from a DataFrame acts as its own copy, so changing it never changes the original.")

PLUS_FIG = """
<svg viewBox="0 0 640 150" role="img" aria-label="x += [2] grows the same list, so y sees it. x = x + [2] builds a new list for x, and y keeps the old one.">
  <defs><marker id="m1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <text x="10" y="18" class="h">x += [2]   (in place)</text>
  <rect x="10" y="40" width="40" height="28" rx="8" class="box"/><text x="30" y="59" class="tk">x</text>
  <rect x="10" y="92" width="40" height="28" rx="8" class="box"/><text x="30" y="111" class="tk">y</text>
  <rect x="140" y="62" width="120" height="38" rx="10" class="box a"/><text x="200" y="86" class="w mid">[1, 2]</text>
  <path d="M50 54 L136 76" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#m1)"/>
  <path d="M50 106 L136 88" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#m1)"/>
  <text x="200" y="128" class="mid">same object, y sees [1, 2]</text>
  <text x="340" y="18" class="h">x = x + [2]   (new object)</text>
  <rect x="340" y="40" width="40" height="28" rx="8" class="box"/><text x="360" y="59" class="tk">x</text>
  <rect x="340" y="92" width="40" height="28" rx="8" class="box"/><text x="360" y="111" class="tk">y</text>
  <rect x="470" y="32" width="130" height="36" rx="10" class="box b"/><text x="535" y="55" class="w mid">[1, 2]  new</text>
  <rect x="470" y="90" width="130" height="36" rx="10" class="box a"/><text x="535" y="113" class="w mid">[1]  old</text>
  <path d="M380 54 L466 50" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#m1)"/>
  <path d="M380 106 L466 108" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#m1)"/>
  <text x="535" y="144" class="mid">y keeps [1]</text>
</svg>"""

section("kinds", "Objects that can change and objects that cannot",
    p("""Every object is either **mutable** (it can be changed in place after it is created) or **immutable** (it can
    never change). When an object changes in place, its identity stays the same: same `id()`, same object, new
    contents. When you "change" an immutable value, Python builds a new object and moves the name, exactly like the
    rebinding you saw in 2.1."""),
    html("""<div class="tbl"><table>
      <tr><th>Mutable: can change in place</th><th>Immutable: never changes</th></tr>
      <tr><td><code>list</code>, <code>dict</code>, <code>set</code>, <code>bytearray</code></td><td><code>int</code>, <code>float</code>, <code>bool</code>, <code>complex</code>, <code>None</code></td></tr>
      <tr><td>most objects of your own classes</td><td><code>str</code>, <code>bytes</code></td></tr>
      <tr><td>numpy arrays, pandas DataFrames and Series</td><td><code>tuple</code>, <code>frozenset</code> (but see the tuple trap below)</td></tr>
    </table></div>"""),
    ex("""
    xs = [1, 2]
    before = id(xs)
    xs.append(3)               # changes the list itself
    print(xs, id(xs) == before)

    s = "data"
    before = id(s)
    s = s.upper()              # str cannot change: a new string, name moved
    print(s, id(s) == before)
    """, "in_place.py"),
    p("""A useful convention follows from this: in the standard library, **methods that change an object in place
    return `None`**. `list.sort()`, `list.append()`, `dict.update()`, `set.add()` and `random.shuffle()` all return
    `None`. Functions that leave their input alone and build something new return it: `sorted()`, `reversed()`,
    `str.upper()`. Writing `xs = xs.sort()` therefore replaces your list with `None` (problem 3)."""),
    p("""It is worth knowing the full list of in-place list operations, because each one changes the object every alias sees:
    `append`, `extend`, `insert`, `pop`, `remove`, `clear`, `sort`, `reverse`, `del xs[i]`, `xs[i] = v`, and **slice
    assignment**, `xs[:] = new_items`. The last one is the subtle one. `xs = new_items` rebinds the name and leaves the old
    list alone, while `xs[:] = new_items` keeps the same list object and replaces its **contents**, so every alias sees the
    new items. Code that "resets" a shared list has to choose between the two on purpose."""),
    ex("""
    shared = [1, 2, 3]
    alias = shared
    shared = [9]                   # rebinding: alias still sees the old list
    print(alias)

    shared = alias
    shared[:] = [9]                # slice assignment: same object, new contents
    print(alias, alias is shared)
    """, "slice_assign.py"),
    p("""Why have immutable types at all? Three reasons, all practical. An immutable object can be **shared safely**: you can pass
    a string or a tuple anywhere without worrying that someone will change it under you. It can be **hashed**, which is what
    dict keys and set members need: a key's hash must never change, or the dict could no longer find it (4.5). And it is
    simpler to reason about in concurrent code, since two threads cannot race to change it. When you need a read-only
    version of a mutable type, Python has some: `tuple` for lists, `frozenset` for sets, and `types.MappingProxyType(d)`,
    a read-only **view** of a dict that reflects changes to `d` but refuses writes through itself."""),
    ex("""
    from types import MappingProxyType

    _settings = {"model": "small"}
    SETTINGS = MappingProxyType(_settings)
    try:
        SETTINGS["model"] = "large"
    except TypeError as e:
        print("TypeError:", e)
    _settings["model"] = "medium"            # the owner can still change it
    print(SETTINGS["model"], frozenset({"a", "b"}) == frozenset({"b", "a"}))
    """, "read_only.py"),
)

section("aliasing", "Aliasing: one object, several names",
    p("""**Aliasing** means two or more names, or container slots, point at the same object. With immutable objects
    aliasing is harmless, because nobody can change the object. With mutable objects every change made through any of
    the names is visible through all of them, because there is only one object."""),
    ex("""
    config = {"model": "small", "temperature": 0.2}
    run_a = config                 # an alias, not a copy
    run_a["temperature"] = 0.9
    print(config["temperature"])   # the "original" changed too

    defaults = {"retries": 3}
    settings = {"api": defaults, "batch": defaults}   # both slots point at one dict
    settings["api"]["retries"] = 5
    print(settings["batch"]["retries"])
    """, "aliasing.py"),
    p("""Aliases hide in places that do not look like assignment:"""),
    p("""- **Containers:** putting the same list or dict into two slots (above), or `dict.fromkeys(keys, [])`, which uses
      one list for every key (problem 5).
    - **Return values:** a function that returns its internal list hands the caller a way to change its state
      (problem 6).
    - **Repetition:** `[[]] * 3` repeats one inner list three times (the grid trap; lesson 2.3 shows the fix).
    - **Default arguments and function arguments** (lesson 2.4)."""),
    callout("sql", "SQL / Power BI", """An alias is like two Power BI visuals bound to the **same** measure. Edit the
    measure and both visuals change, because there is one measure, not two. A copy is like duplicating the measure
    under a new name: editing one no longer touches the other."""),
    p("""Aliasing also happens **in time**: the same list being changed while it is being read. Removing items from a list while a
    `for` loop walks over it skips items, because the loop keeps an index into the list and every removal shifts the
    remaining items one place to the left, under the index. The loop then steps over the item that moved into the gap. The
    fix is to build a new list (a comprehension, 6.1), or to loop over a copy, `for x in xs[:]`."""),
    ex("""
    scores = [0.2, 0.1, 0.9, 0.3, 0.05]
    for s in scores:
        if s < 0.5:
            scores.remove(s)               # changing the list being iterated
    print(scores)                          # 0.1 and 0.05 survived

    scores = [0.2, 0.1, 0.9, 0.3, 0.05]
    print([s for s in scores if s >= 0.5]) # a new list instead
    """, "mutate_while_iterating.py"),
    p("""Step by step: the loop reads index 0 (`0.2`), removes it, and everything shifts left, so `0.1` is now at index 0. The loop
    moves on to index 1, which now holds `0.9`, so `0.1` is never checked. The same happens to `0.05` after `0.3` is removed.
    Dicts and sets protect themselves: changing their size during iteration raises `RuntimeError: dictionary changed size during
    iteration`, which is noisier but much safer."""),
)

section("operators", "Changing versus rebinding: `+=`, `+` and friends",
    p("""For a list, `x += y` changes the list **in place** (it is `x.extend(y)` under the hood), while `x = x + y`
    builds a **new** list and moves the name. With an alias around, they give different results. For immutable types
    there is no in-place version, so `+=` on a str, tuple or int always builds a new object."""),
    ex("""
    x = [1]; y = x
    x += [2]                      # in place: y sees it
    print(x, y, x is y)

    x = [1]; y = x
    x = x + [2]                   # new list: y keeps the old one
    print(x, y, x is y)

    t = (1,); u = t
    t += (2,)                     # tuple: always a new object
    print(t, u)
    """, "plus_equals.py"),
    fig(PLUS_FIG, "`+=` on a list changes the object both names share. `x = x + [2]` builds a new list for `x` only."),
    p("""The mechanism behind this: `x += y` first asks the type of `x` for an **in-place add** (the method `__iadd__`). Lists,
    dicts (`|=`), sets (`|=`, `&=`, `-=`), numpy arrays and DataFrames provide one, so the object changes and the name is then
    re-bound to the same object. If the type has no in-place version, as for `int`, `str` and `tuple`, Python falls back to
    `x = x + y`: it builds a new object and rebinds the name. The same rule covers `-=`, `*=`, `|=` and the others."""),
    p("""One famous consequence combines everything so far. `t[0] += [3]`, where `t` is a tuple holding a list, first extends the
    list in place (that succeeds), then tries to store the result back into `t[0]` (that fails, because tuples cannot be
    assigned to). You get a `TypeError` **and** the list has changed."""),
    ex("""
    t = ([1, 2], "label")
    try:
        t[0] += [3]
    except TypeError as e:
        print("TypeError:", e)
    print(t)                              # the list changed anyway

    import numpy as np
    a = np.array([1.0, 2.0]); b = a
    a *= 10                               # in place on the shared array
    print(b)
    """, "iadd_details.py"),
)

section("tuples", "Tuples are immutable, their contents may not be",
    p("""A tuple cannot change **which objects** it holds: you cannot assign `t[0] = ...`. But if one of those objects is
    mutable, that object can still change in place. So a tuple is only "frozen" all the way down if everything inside
    it is immutable too. That is also the rule for using a tuple as a dict key or set member: `(1, "a")` works,
    `([1], "a")` raises `TypeError: unhashable type: 'list'`."""),
    ex("""
    t = ([1, 2], "label")
    t[0].append(3)                # the list inside can change
    print(t)
    try:
        hash(t)
    except TypeError as e:
        print("TypeError:", e)
    print(hash((1, "label")) == hash((1, "label")))
    """, "tuple_contents.py"),
    p("""The hash rule is the reason. A tuple's hash is computed from the hashes of its items, so if an item could change, the
    tuple's hash would change with it, and a dict that stored the tuple as a key would look for it in the wrong place. Python
    therefore refuses to hash a tuple that contains anything unhashable. When you need a composite key with a "set-like" part,
    such as a combination of tags, use a `frozenset`, which is hashable and ignores order."""),
    ex("""
    runs = {}
    runs[("small", frozenset({"eu", "prod"}))] = 0.91
    print(runs[("small", frozenset({"prod", "eu"}))])     # order of tags does not matter
    """, "hashable_keys.py"),
)

section("views", "numpy views and pandas 3 Copy-on-Write",
    p("""Data libraries make aliasing more important, because copying big arrays is expensive. **numpy** returns a
    **view** for basic slicing: a new array object that looks at the same memory. Changing the view changes the
    original. Boolean masks and lists of indexes ("fancy indexing") return a copy instead."""),
    ex("""
    import numpy as np

    a = np.arange(6)
    first = a[:3]                 # basic slice: a view
    first[0] = 99
    print(a, np.shares_memory(a, first))

    picked = a[a > 3]             # boolean mask: a copy
    picked[0] = -1
    print(a, np.shares_memory(a, picked))
    """, "numpy_views.py"),
    p("""Other numpy operations return views too: `reshape` (when the memory layout allows it), the transpose `a.T`, and
    `a.ravel()` in the common case. When you need an independent array, call `.copy()` explicitly. That is cheap insurance in
    two situations: when you slice a small part of a huge array and want to keep only the part (the view keeps the whole big
    buffer alive, 2.1), and when you hand an array to code that might change it."""),
    ex("""
    import numpy as np

    big = np.zeros(1_000_000)
    small_view = big[:3]
    small_copy = big[:3].copy()
    print(small_view.base is big, small_copy.base is None)
    m = np.arange(6).reshape(2, 3)
    m.T[0, 0] = 42
    print(m[0, 0], np.shares_memory(m, m.T))
    """, "numpy_more_views.py"),
    p("""**pandas** used to behave in a confusing mix of views and copies, which is what `SettingWithCopyWarning` was
    about. **pandas 3.0 made Copy-on-Write the only behaviour**: anything you take out of a DataFrame (a column, a
    filtered subset) acts as its own copy, so changing it never changes the original. To change the original, change it
    directly with `.loc`."""),
    ex("""
    import pandas as pd

    df = pd.DataFrame({"x": [1, 2, 3]})
    sub = df[df["x"] > 1]
    sub["x"] = 0                  # changes sub only
    col = df["x"]
    col.iloc[0] = 100             # changes col only
    print(df["x"].tolist(), sub["x"].tolist(), col.tolist())

    df.loc[df["x"] > 1, "x"] = 7  # the way to change df itself
    print(df["x"].tolist())
    print(pd.__version__)
    """, "pandas_cow.py"),
    callout("warn", "Old tutorials are wrong now", """Many tutorials, Stack Overflow answers and older code were written
    for pandas 1.x and 2.x, where `col = df["x"]; col.iloc[0] = 100` **did** change `df`, and chained assignment like
    `df["x"][1] = 5` sometimes worked. In pandas 3 that chained form silently does nothing to `df` and only emits a
    `ChainedAssignmentError` warning. Always write `df.loc[row, "x"] = value`."""),
)

section("warmup", "Warm-up",
    predict("An alias and a number", "easy",
        code="""
        scores = [90, 85]
        backup = scores
        scores.append(70)
        print(backup)

        total = 175
        saved = total
        total += 70
        print(saved, total)
        print(id(scores) == id(backup))
        """,
        hints=["`append` changes the list both names point at. `+=` on an int cannot change the int."],
        why="""`backup = scores` is an alias, so the `append` shows through `backup`. `total += 70` builds a new int and
        moves only `total`; `saved` keeps 175. Same syntax family, opposite behaviour, because a list can change and an int
        cannot."""),
    predict("`+=` versus `+`", "easy",
        code="""
        a = [1]; b = a
        a += [2]
        print(a, b)

        c = [1]; d = c
        c = c + [2]
        print(c, d)

        s = "ab"; r = s
        s += "c"
        print(s, r)
        """,
        hints=["Which of these types can change in place?"],
        why="""`a += [2]` extends the shared list, so `b` sees it. `c = c + [2]` builds a new list for `c` only. A string
        cannot change, so `s += "c"` builds a new string and `r` keeps `"ab"`. When you read `x += y`, always ask
        whether `x` is mutable: that decides whether other names see the change."""),
    fix("Top-k scores that return None", "easy", tag="ML",
        prompt="""`top_k` should return the `k` highest similarity scores, highest first, **without changing the caller's
        list** (the caller still needs the scores in document order). It crashes. Fix it so both tests pass.""",
        code="""
        def top_k(scores, k):
            ranked = scores.sort(reverse=True)
            return ranked[:k]
        """,
        tests="""
        sims = [0.12, 0.91, 0.45, 0.78]
        assert top_k(sims, 2) == [0.91, 0.78]
        assert sims == [0.12, 0.91, 0.45, 0.78]
        assert top_k(sims, 0) == []
        assert top_k([], 3) == []
        """,
        hints=["What does `list.sort()` return?", "Even after fixing the return value, `sort()` would reorder the caller's list. Which function builds a new list?"],
        solution="""
        def top_k(scores, k):
            return sorted(scores, reverse=True)[:k]
        """,
        why="""`scores.sort()` sorts in place and returns `None`, so `ranked[:k]` fails with `TypeError: 'NoneType' object is
        not subscriptable`. Changing it to `scores.sort(...); return scores[:k]` would pass the first test and silently
        break the caller, whose list is now reordered (the second test). `sorted()` builds a new list and leaves the input
        alone. For large arrays, `heapq.nlargest(k, scores)` or `np.argpartition` avoid sorting everything (Module 16)."""),
    write("Normalise in place", "easy", tag="ML",
        prompt="""Write `normalise_inplace(weights)` that divides every value by the total so they sum to 1, **changing the
        same list** (other code holds a reference to it) and returning `None`, like the standard library's in-place
        methods. A total of 0 should raise `ValueError`.""",
        code="""
        def normalise_inplace(weights):
            pass
        """,
        tests="""
        import math
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        w = [1, 1, 2]
        ref = w
        assert normalise_inplace(w) is None
        assert ref is w and w == [0.25, 0.25, 0.5]
        v = [0.2, 0.3]
        normalise_inplace(v)
        assert math.isclose(sum(v), 1.0)
        assert raises(ValueError, normalise_inplace, [0, 0])
        """,
        hints=["`weights = [...]` would only move your local name. You need to change the list object itself.",
               "Either write each position `weights[i] = ...`, or replace all the contents at once with `weights[:] = [...]`."],
        solution="""
        def normalise_inplace(weights):
            total = sum(weights)
            if total == 0:
                raise ValueError("weights sum to 0")
            weights[:] = [w / total for w in weights]
        """,
        why="""`weights[:] = new_list` replaces the **contents** of the existing list, so every alias sees the new
        values. A plain `weights = [...]` inside the function would create a new list visible only inside the function,
        and the caller's list would stay unchanged (lesson 2.4 explains why). Returning `None` signals "I changed your
        object", the same promise `list.sort()` makes. Choosing in place versus returning a new list is an API decision:
        in place saves memory for huge data, returning new is safer to reason about."""),
)

section("medium", "Medium",
    predict("`dict.fromkeys` with a list", "medium", tag="Data work",
        code="""
        buckets = dict.fromkeys(["pos", "neg"], [])
        buckets["pos"].append("great")
        print(buckets)
        print(buckets["pos"] is buckets["neg"])

        fixed = {k: [] for k in ["pos", "neg"]}
        fixed["pos"].append("great")
        print(fixed)
        """,
        hints=["`dict.fromkeys(keys, value)` evaluates `value` once. How many lists exist?"],
        why="""`dict.fromkeys` stores the **same** list object under every key, so appending for `"pos"` also shows
        under `"neg"`. The dict comprehension evaluates `[]` once per key, giving separate lists. `fromkeys` is fine with
        immutable defaults like `0` or `None`; for lists, use a comprehension or `collections.defaultdict(list)`
        (lesson 4.6)."""),
    fix("The chat store that leaks", "medium", tag="GenAI",
        prompt="""A tiny in-memory chat store. A caller fetched the messages, appended a **draft** to build a prompt, and
        the draft ended up saved in the store. Fix `get_messages` so callers cannot change the store's data by changing
        what they get back.""",
        code="""
        _store = {"c1": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello!"}]}

        def get_messages(chat_id):
            return _store[chat_id]

        def add_message(chat_id, role, content):
            _store[chat_id].append({"role": role, "content": content})
        """,
        tests="""
        msgs = get_messages("c1")
        msgs.append({"role": "user", "content": "draft, not sent"})
        assert len(get_messages("c1")) == 2
        add_message("c1", "user", "thanks")
        assert [m["content"] for m in get_messages("c1")] == ["hi", "Hello!", "thanks"]
        assert get_messages("c1") is not get_messages("c1")
        """,
        hints=["Return a new list that holds the same messages: `list(...)` or a slice `[:]`."],
        solution="""
        _store = {"c1": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello!"}]}

        def get_messages(chat_id):
            return list(_store[chat_id])

        def add_message(chat_id, role, content):
            _store[chat_id].append({"role": role, "content": content})
        """,
        why="""Returning the internal list returns an alias, so any caller can change the store by accident. `list(...)`
        returns a new list, so appending to it no longer touches the store. Note what is **not** fixed: both lists still
        hold the same message dicts, so `msgs[0]["content"] = "x"` would still change the store. That is a shallow
        copy, and lesson 2.3 is about when you need a deep one. Another option is to return a tuple, which callers
        cannot append to at all."""),
    trace("Sorting, rebinding and `+=`", "medium",
        prompt="Fill in `a`, `b` and `a is b` after each line.",
        code="""
        a = [3, 1, 2]
        b = a  # row: "b = a"
        a.sort()  # row: "a.sort()"
        a = sorted(a, reverse=True)  # row: "a = sorted(a, reverse=True)"
        b += [0]  # row: "b += [0]"
        a[0] = b  # row: "a[0] = b"
        """,
        trace_vars=["a", "b", "a is b"],
        hints=["`sort()` changes the shared list. `sorted()` builds a new one. `+=` on a list changes it in place.",
               "In the last line, `a[0]` is set to the list object `b` itself."],
        why="""`a.sort()` sorts the one shared list, so `b` changes too. `sorted(...)` builds a new list for `a`, ending the
        alias. `b += [0]` extends `b` in place; `a` is a different list now, so it does not change. The last line stores the
        list `b` inside `a`, so `a` prints as `[[1, 2, 3, 0], 2, 1]` and still is not `b`: an alias now lives inside a
        container."""),
    write("Remove duplicates in place", "medium", tag="Data work",
        prompt="""Write `dedupe_inplace(rows)` that removes repeated values from a list of hashable values, keeping the
        **first** occurrence and the original order. It must change **the same list object**, because a pipeline holds
        references to it, and return `None`.""",
        code="""
        def dedupe_inplace(rows):
            pass
        """,
        tests="""
        rows = ["a", "b", "a", "c", "b"]
        ref = rows
        assert dedupe_inplace(rows) is None
        assert ref is rows and rows == ["a", "b", "c"]
        empty = []
        dedupe_inplace(empty)
        assert empty == []
        nums = [3, 3, 3]
        dedupe_inplace(nums)
        assert nums == [3]
        """,
        hints=["Build the deduplicated list first (a `seen` set plus a new list), then put it back into the same object.",
               "`dict.fromkeys(rows)` keeps the first occurrence of each key, in order."],
        solution="""
        def dedupe_inplace(rows):
            rows[:] = dict.fromkeys(rows)
        """,
        why="""`dict.fromkeys(rows)` keeps each value once, in first-seen order (dicts keep insertion order), and slice
        assignment `rows[:] = ...` puts the result into the existing list, so every alias sees it. Deleting items while
        looping (`for x in rows: rows.remove(x)`) is the classic mistake from 1.2. The slice-assignment pattern is the safe
        way to "change a list in place" with any new contents."""),
    choose("Growing a list in a loop", "medium",
        prompt="Both build the list of squares for 10,000 numbers. Which is faster?",
        setup="n = 10000",
        options={
            "a": "out = []\nfor i in range(n):\n    out = out + [i * i]",
            "b": "out = []\nfor i in range(n):\n    out.append(i * i)",
        },
        answer="b",
        hints=["`out + [i * i]` builds a whole new list each time. How many items get copied in total?"],
        why="""A copies the entire list on every pass: 1 + 2 + ... + n items, which is O(n²). B changes one list in place,
        and `append` is O(1) on average, so the whole loop is O(n). The same trap exists for strings (`s = s + piece` in a
        loop), with `"".join(parts)` as the fix (Module 5)."""),
    fix("Features added twice", "medium", tag="ML",
        prompt="""`add_bias` adds a constant `1.0` feature to every row before training. The pipeline calls it once for
        the training rows and once more inside cross-validation, and the second call finds rows that already have the bias.
        It also changes the raw data the caller wanted to keep. Make it return new rows and leave the input untouched.""",
        code="""
        def add_bias(rows):
            for row in rows:
                row.append(1.0)
            return rows
        """,
        tests="""
        raw = [[0.5, 2.0], [1.5, 3.0]]
        out = add_bias(raw)
        assert out == [[0.5, 2.0, 1.0], [1.5, 3.0, 1.0]]
        assert raw == [[0.5, 2.0], [1.5, 3.0]]
        assert add_bias(raw) == out
        assert out is not raw and out[0] is not raw[0]
        """,
        hints=["Build each new row with `row + [1.0]` instead of `row.append(1.0)`."],
        solution="""
        def add_bias(rows):
            return [row + [1.0] for row in rows]
        """,
        why="""The original changes every row object in place, and because it returns the same list, the "output" and the
        raw data are aliases. A second call appends a second bias. This is how leakage and double transformations sneak
        into ML pipelines: no error, just wrong features. scikit-learn's scalers follow the same rule: `transform` returns a
        new array and leaves the input alone, unless you explicitly pass `copy=False`."""),
    fix("Overrides that stick", "medium", tag="GenAI",
        prompt="""`make_config(overrides)` should return the default LLM settings with some values overridden for one run.
        After one call with `temperature=0.9`, every later call also gets 0.9. Fix it so `DEFAULTS` never changes.""",
        code="""
        DEFAULTS = {"model": "small", "temperature": 0.2, "max_tokens": 512}

        def make_config(overrides):
            cfg = DEFAULTS
            for key, value in overrides.items():
                cfg[key] = value
            return cfg
        """,
        tests="""
        a = make_config({"temperature": 0.9})
        b = make_config({})
        assert a == {"model": "small", "temperature": 0.9, "max_tokens": 512}
        assert b == {"model": "small", "temperature": 0.2, "max_tokens": 512}
        assert DEFAULTS["temperature"] == 0.2
        assert a is not DEFAULTS and b is not DEFAULTS
        """,
        hints=["`cfg = DEFAULTS` is an alias. You need a new dict that starts from the defaults.",
               "`{**DEFAULTS, **overrides}` or `DEFAULTS | overrides` (Python 3.9+) both build a new dict."],
        solution="""
        DEFAULTS = {"model": "small", "temperature": 0.2, "max_tokens": 512}

        def make_config(overrides):
            return DEFAULTS | overrides
        """,
        why="""`cfg = DEFAULTS` makes `cfg` another name for the module's one defaults dict, so every override is written
        into the defaults themselves and leaks into all later runs: non-reproducible experiments with no error message.
        `DEFAULTS | overrides` builds a new dict with the right side winning. This is shallow: a nested dict inside
        `DEFAULTS` would still be shared (lesson 2.3). To make the defaults impossible to change by accident, wrap them in
        `types.MappingProxyType(...)`, a read-only view of a dict."""),
    refactor("Clean tokens in place, without the manual index", "medium",
        prompt="""This strips and lower-cases tokens and drops empty ones, changing the list in place (callers rely on
        that) and returning it. The manual index loop is hard to read and easy to break. Rewrite it so it still changes
        the same list object. Keep the tests green.""",
        code="""
        def clean_tokens(tokens):
            i = 0
            while i < len(tokens):
                if tokens[i].strip() == "":
                    del tokens[i]
                else:
                    tokens[i] = tokens[i].strip().lower()
                    i = i + 1
            return tokens
        """,
        tests="""
        t = [" Hello", "", "WORLD ", "   ", "ok"]
        ref = t
        out = clean_tokens(t)
        assert out is t and ref is t
        assert t == ["hello", "world", "ok"]
        assert clean_tokens([]) == []
        """,
        hints=["Build the cleaned list with a comprehension, then assign it into the same object with `tokens[:] = ...`."],
        solution="""
        def clean_tokens(tokens):
            tokens[:] = [t.strip().lower() for t in tokens if t.strip()]
            return tokens
        """,
        why="""The original only works because it carefully does not advance `i` after a delete, which is the bug-prone
        part of changing a list while walking it (1.2). The comprehension builds the result in one readable step, and
        `tokens[:] =` keeps the in-place contract. Returning the same list as well as changing it is a style choice some
        libraries make for chaining; the standard library's own in-place methods return `None` instead."""),
    predict("numpy: view or copy?", "medium", tag="ML",
        code="""
        import numpy as np

        x = np.arange(6)
        head = x[:3]
        head[0] = 99
        print(x)

        safe = x[:3].copy()
        safe[1] = -1
        print(x)

        big = x[x > 3]
        big[0] = 0
        print(x)

        every_other = x[::2]
        every_other[:] = 7
        print(x)
        """,
        hints=["Basic slices (`a:b`, `a:b:step`) are views. Boolean masks are copies. `.copy()` always copies."],
        why="""`x[:3]` is a view, so setting `head[0]` changes `x`. `.copy()` breaks the link. The boolean mask `x[x > 3]`
        makes a copy, so changing `big` does nothing to `x`. `x[::2]` is a strided view, so `every_other[:] = 7` writes 7
        into positions 0, 2 and 4 of `x`. This is why a "preprocessing" step that slices an array and then normalises
        the slice can silently change your training data."""),
)

section("hard", "Hard",
    predict("The tuple that changes and raises", "hard",
        code="""
        t = ([1], 2)
        try:
            t[0] += [3]
        except TypeError as e:
            print("TypeError:", e)
        print(t)
        """,
        hints=["`t[0] += [3]` is really two steps: extend the list in place, then store the result back into `t[0]`.",
               "Which of those two steps can a tuple refuse?"],
        why="""`t[0] += [3]` runs as `tmp = t[0]; tmp = tmp.__iadd__([3]); t[0] = tmp`. The first part extends the list
        **in place**, and it succeeds. Then Python tries to store the result back into `t[0]`, which a tuple refuses, so you
        get the `TypeError`. But the list already changed. An operation that raises and still has its effect is very
        surprising, and this is a famous interview puzzle. `t[0].extend([3])` does the same change without the error."""),
    predict("pandas 3: what changes the DataFrame?", "hard", tag="ML",
        code="""
        import pandas as pd

        df = pd.DataFrame({"score": [0.2, 0.9, 0.5], "label": ["a", "b", "c"]})
        high = df[df["score"] > 0.4]
        high["label"] = "HIGH"
        print(df["label"].tolist())

        scores = df["score"]
        scores.iloc[0] = 1.0
        print(df["score"].tolist())

        df.loc[df["score"] > 0.4, "label"] = "HIGH"
        print(df["label"].tolist())
        """,
        hints=["pandas 3 always uses Copy-on-Write: anything you take out of `df` behaves as its own copy.",
               "Only one of these statements writes to `df` itself."],
        why="""With Copy-on-Write, `high` and `scores` behave as independent copies the moment you change them, so the first
        two changes do not reach `df`. In pandas 2.x and older the second one (`scores.iloc[0] = 1.0`) **did** change
        `df`, and the first one raised `SettingWithCopyWarning`. `df.loc[mask, "label"] = ...` is the one statement that
        writes to `df`, and it is the correct way in every version. If you maintain old pipeline code, this upgrade can
        silently change results: look for code that relied on a column or slice writing back into its DataFrame."""),
    fix("Read the code: embedding batches", "hard", tag="GenAI",
        prompt="""This splits texts into batches for an embedding API, with at most `max_items` texts and at most
        `max_tokens` (rough count: words) per batch. Each batch also gets a small metadata dict. The output is wrong in
        two ways that both come from aliasing. Read the whole function, find both bugs and fix them.""",
        code="""
        def count_tokens(text):
            return len(text.split())


        def make_batches(texts, max_items, max_tokens):
            batches = []
            batch = []
            meta = {"tokens": 0, "items": 0}
            for text in texts:
                n = count_tokens(text)
                if batch and (len(batch) == max_items or meta["tokens"] + n > max_tokens):
                    batches.append({"texts": batch, "meta": meta})
                    batch.clear()
                    meta["tokens"] = 0
                    meta["items"] = 0
                batch.append(text)
                meta["tokens"] += n
                meta["items"] += 1
            if batch:
                batches.append({"texts": batch, "meta": meta})
            return batches
        """,
        tests="""
        texts = ["a b", "c d e", "f", "g h i j", "k"]
        out = make_batches(texts, max_items=2, max_tokens=5)
        assert [b["texts"] for b in out] == [["a b", "c d e"], ["f", "g h i j"], ["k"]]
        assert [b["meta"] for b in out] == [{"tokens": 5, "items": 2}, {"tokens": 5, "items": 2}, {"tokens": 1, "items": 1}]
        assert out[0]["texts"] is not out[1]["texts"] and out[0]["meta"] is not out[1]["meta"]
        assert make_batches([], 2, 5) == []
        """,
        hints=["After `batches.append({\"texts\": batch, ...})`, what does `batch.clear()` do to the list just stored?",
               "The same question for `meta`: how many meta dicts exist in the whole run?",
               "Start a fresh list and a fresh dict instead of clearing the old ones."],
        solution="""
        def count_tokens(text):
            return len(text.split())


        def make_batches(texts, max_items, max_tokens):
            batches = []
            batch = []
            meta = {"tokens": 0, "items": 0}
            for text in texts:
                n = count_tokens(text)
                if batch and (len(batch) == max_items or meta["tokens"] + n > max_tokens):
                    batches.append({"texts": batch, "meta": meta})
                    batch = []
                    meta = {"tokens": 0, "items": 0}
                batch.append(text)
                meta["tokens"] += n
                meta["items"] += 1
            if batch:
                batches.append({"texts": batch, "meta": meta})
            return batches
        """,
        why="""`batches.append({"texts": batch, ...})` stores a reference to the list, not a snapshot. `batch.clear()` then
        empties that very list, and the loop keeps appending to it, so every stored batch is the **same** list. The
        metadata has the same bug: one `meta` dict is shared by all batches and reset in place. The fix is to bind the
        names to **new** objects (`batch = []`, `meta = {...}`) so the stored ones are left alone. "Reuse and clear" is
        a common habit from languages without garbage collection, and in Python it turns into aliasing bugs. Sent to a
        real embedding API, the buggy version would embed the wrong texts with no error at all."""),
    write("Hashable cache keys from tool arguments", "hard", tag="GenAI",
        prompt="""An agent caches tool results keyed by the tool's arguments, which arrive as JSON-like data: dicts,
        lists, strings, numbers, booleans and `None`, nested to any depth. Dicts and lists are mutable, so they cannot be
        dict keys. Write `freeze(value)` that turns such data into an equivalent **hashable** value: lists become tuples,
        dicts become a tuple of `(key, frozen_value)` pairs sorted by key, and everything else stays as it is. Two inputs
        that are equal (whatever the key order) must give equal results.""",
        code="""
        def freeze(value):
            pass
        """,
        tests="""
        a = {"query": "refund", "filters": {"year": 2025, "tags": ["billing", "eu"]}, "k": 5}
        b = {"k": 5, "filters": {"tags": ["billing", "eu"], "year": 2025}, "query": "refund"}
        assert freeze(a) == freeze(b)
        assert hash(freeze(a)) == hash(freeze(b))
        cache = {freeze(a): "result"}
        assert cache[freeze(b)] == "result"
        assert freeze({"q": ["x", "y"]}) != freeze({"q": ["y", "x"]})
        assert freeze([1, [2, None]]) == (1, (2, None))
        assert freeze("text") == "text"
        """,
        hints=["Handle three cases: dict, list, anything else. The dict and list cases call `freeze` on their contents.",
               "`sorted(d.items())` sorts the pairs by key. Freeze each value inside the pairs."],
        solution="""
        def freeze(value):
            if isinstance(value, dict):
                return tuple(sorted((k, freeze(v)) for k, v in value.items()))
            if isinstance(value, list):
                return tuple(freeze(v) for v in value)
            return value
        """,
        why="""Hashing needs the value to never change, so every mutable layer has to become an immutable one, at every
        depth: that is why it must recurse. Sorting the dict pairs makes key order irrelevant, matching dict equality,
        while list order is kept because `["x", "y"]` and `["y", "x"]` are different arguments. A common shortcut is
        `json.dumps(value, sort_keys=True)` as the key, which also works and is easy to log. It is slower and treats
        `1` and `1.0` differently, while `freeze` treats them as equal, which is the same rule dicts use. Pick the one
        whose equality matches what you want cached."""),
    predict("Aliases inside a grid", "hard",
        code="""
        row = [0] * 3
        grid = [row, row]
        grid[0][0] = 1
        print(grid)

        grid[1] = grid[1] + [9]
        grid[0].append(5)
        print(grid)
        print(grid[0] is row, grid[1] is row)
        """,
        hints=["Both slots start as the same list. Which line gives slot 1 its own list?"],
        why="""`grid = [row, row]` has two slots pointing at one list, so `grid[0][0] = 1` shows in both rows.
        `grid[1] + [9]` builds a **new** list and stores it in slot 1, which ends the alias for that slot. `append` then
        changes only the original `row`, which is still in slot 0. After that line `row` is `[1, 0, 0, 5]` and slot 1 is
        `[1, 0, 0, 9]`. This is the `[[0] * 3] * 3` trap in slow motion; lesson 2.3 shows how to build grids safely."""),
)

section("interview", "Interview questions",
    explain("Which built-in types are mutable, and why does it matter?", "medium", tag="Interview",
        why="""Mutable: list, dict, set, bytearray, and most user-defined objects. Immutable: int, float, bool, complex,
        str, bytes, tuple, frozenset, None. It matters in three places. First, **aliasing**: any name or container that
        shares a mutable object sees every change, which causes action-at-a-distance bugs. Second, **hashing**: only values
        that cannot change can be dict keys or set members, because a key whose hash changed could never be found again.
        Third, **defaults and arguments**: a mutable default argument is created once and shared between calls (lesson
        2.4). A strong answer adds that a tuple is only as immutable as its contents, and mentions numpy views and pandas
        Copy-on-Write for data roles."""),
    explain("Explain what happens in `t = ([1], 2); t[0] += [3]`.", "hard", tag="Interview",
        why="""It raises `TypeError: 'tuple' object does not support item assignment`, **and** `t` becomes `([1, 3], 2)`.
        Augmented assignment on an item is two steps: call `t[0].__iadd__([3])`, which extends the list in place and
        succeeds, then assign the result back to `t[0]`, which the tuple refuses. The interviewer wants to hear that you
        know `+=` on a list is in place, and that a tuple's immutability only covers which objects it holds, not those
        objects' contents. Mention that `t[0].extend([3])` makes the same change without raising."""),
    explain("What was `SettingWithCopyWarning`, and what changed in pandas 3?", "hard", tag="Interview",
        why="""In pandas 1.x and 2.x, indexing could return either a view of the DataFrame or a copy, and it was hard to
        predict which. Writing to a result that might be a copy, such as `sub = df[mask]; sub["x"] = 0` or chained
        assignment `df[mask]["x"] = 0`, raised `SettingWithCopyWarning` because the write might or might not reach `df`.
        pandas 3.0 made **Copy-on-Write** the only behaviour: every object you derive from a DataFrame behaves as its own
        copy, copying lazily only when one side is changed. So writes to derived objects never reach the original, the
        warning is gone, and chained assignment never works (it warns with `ChainedAssignmentError`). The correct way to
        change `df` in every version is `df.loc[mask, "x"] = 0`. Bonus: Copy-on-Write also saves memory, because derived
        objects share data until someone writes."""),
)

recap(
    "Mutable objects (list, dict, set, arrays, DataFrames) change in place and keep their identity. Immutable ones never change: \"changing\" them builds a new object.",
    "Standard-library methods that change an object in place return `None`: `xs = xs.sort()` loses your list. Use `sorted()` for a new one.",
    "Aliases hide in containers, return values, `dict.fromkeys(keys, [])` and `[[]] * n`. Return new objects when callers should not change yours.",
    "On a list, `x += y` changes the shared object; `x = x + y` builds a new one. `xs[:] = ...` replaces the contents in place.",
    "numpy basic slices are views; masks and `.copy()` are copies. pandas 3 is always Copy-on-Write: change a DataFrame only through `df.loc[...]`.",
)
