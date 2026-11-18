from lesson import *

lesson(
    id="m2-3", num="2.3", title="Copies: shallow and deep",
    intro="An alias, a shallow copy and a deep copy are three different things, and nested data (configs, chat "
          "messages, JSON, grids) is where the difference bites. Also: how to avoid copying at all.",
    desc="`copy`, `deepcopy`, slicing, and the `[[0] * 3] * 3` trap.",
    keys="copy shallow deep deepcopy slice list dict copy nested config grid multiplication json roundtrip structural sharing mappingproxytype pandas copy object column memo cycle",
)

term("Shallow copy", "A new outer container holding the same inner objects: `list(x)`, `x[:]`, `x.copy()`, `dict(d)`, `copy.copy(x)`.")
term("Deep copy", "A new container with new copies of everything inside it, at every level: `copy.deepcopy(x)`.")
term("Structural sharing", "Building a changed version of nested data by copying only the path that changes and reusing every untouched part.")

COPY_FIG = """
<svg viewBox="0 0 640 210" role="img" aria-label="A shallow copy is a new outer list whose slots point at the same inner lists. A deep copy also has new inner lists.">
  <defs><marker id="c1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <text x="10" y="18" class="h">Shallow: b = a.copy()</text>
  <rect x="10" y="34" width="90" height="34" rx="9" class="box a"/><text x="55" y="56" class="w mid">a (outer)</text>
  <rect x="10" y="128" width="90" height="34" rx="9" class="box b"/><text x="55" y="150" class="w mid">b (outer)</text>
  <rect x="190" y="60" width="90" height="30" rx="8" class="box"/><text x="235" y="80" class="tk">[1, 2]</text>
  <rect x="190" y="104" width="90" height="30" rx="8" class="box"/><text x="235" y="124" class="tk">[3]</text>
  <path d="M100 48 L186 70" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M100 58 L186 116" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M100 138 L186 80" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M100 148 L186 122" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <text x="150" y="190" class="mid">two outer lists, one set of inner lists</text>
  <text x="340" y="18" class="h">Deep: d = copy.deepcopy(a)</text>
  <rect x="340" y="34" width="90" height="34" rx="9" class="box a"/><text x="385" y="56" class="w mid">a (outer)</text>
  <rect x="340" y="128" width="90" height="34" rx="9" class="box b"/><text x="385" y="150" class="w mid">d (outer)</text>
  <rect x="520" y="26" width="90" height="26" rx="8" class="box"/><text x="565" y="44" class="tk">[1, 2]</text>
  <rect x="520" y="58" width="90" height="26" rx="8" class="box"/><text x="565" y="76" class="tk">[3]</text>
  <rect x="520" y="112" width="90" height="26" rx="8" class="box"/><text x="565" y="130" class="tk">[1, 2] new</text>
  <rect x="520" y="144" width="90" height="26" rx="8" class="box"/><text x="565" y="162" class="tk">[3] new</text>
  <path d="M430 46 L516 40" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M430 56 L516 70" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M430 140 L516 126" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <path d="M430 150 L516 156" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#c1)"/>
  <text x="475" y="198" class="mid">nothing shared</text>
</svg>"""

section("three", "Alias, shallow copy, deep copy",
    p("""There are three different things people mean by "copy", and choosing the wrong one is behind most of the
    aliasing bugs from 2.2:"""),
    p("""- **Alias:** `b = a`. No copy at all, just a second name for the same object.
    - **Shallow copy:** a **new outer container** whose slots point at the **same inner objects**. `list(a)`, `a[:]`,
      `a.copy()`, `dict(d)`, `d.copy()`, `{**d}`, `set(s)` and `copy.copy(x)` are all shallow.
    - **Deep copy:** `copy.deepcopy(x)` copies the outer container **and everything inside it, at every level**, so the
      result shares nothing mutable with the original."""),
    fig(COPY_FIG, "A shallow copy duplicates one level. Changing an inner list through `b` still changes `a`."),
    ex("""
    import copy

    a = [[1, 2], [3]]
    shallow = a.copy()
    deep = copy.deepcopy(a)

    shallow.append([4])          # outer level: only shallow changes
    shallow[0].append(99)        # inner level: shared with a!
    deep[1].append(7)            # deep shares nothing with a
    print(a)
    print(shallow)
    print(deep)
    print(a[0] is shallow[0], a[0] is deep[0])
    """, "shallow_deep.py"),
    p("""A shallow copy is enough when the inner objects are **immutable** (a list of numbers or strings, a dict of
    strings), because nobody can change them anyway. You need a deep copy, or a smarter design, as soon as there is a
    mutable object inside: a list of dicts, a dict of lists, a nested config."""),
    p("""It helps to see exactly what a shallow copy does, step by step. `b = a.copy()` creates a **new, empty list**, then walks
    `a` and puts into `b` a reference to **the same object** that each slot of `a` refers to. It is precisely
    `b = [item for item in a]`. No item is copied; only the outer list is new. So the question "is a shallow copy enough?"
    is the question "will anyone change one of the **items** in place?" For dicts it is the same with values: `d.copy()` is a new
    dict whose keys refer to the same value objects."""),
    p("""The classic place this bites is configuration. An experiment script copies a base config for each run and changes it,
    believing each run has its own settings. But a config is usually nested, and the shallow copy shares the inner dicts, so the
    change to "run 2" also changes the base config and every run that copies it later."""),
    ex("""
    base = {"model": {"name": "small", "temperature": 0.2}, "tags": ["eval"]}

    run2 = base.copy()                       # shallow: new outer dict only
    run2["model"]["temperature"] = 0.9       # changes the SHARED inner dict
    run2["tags"] = ["eval", "hot"]           # rebinding a key: only run2 changes
    print(base["model"]["temperature"], base["tags"])
    print(run2["model"] is base["model"], run2["tags"] is base["tags"])
    """, "shallow_config.py"),
    p("""The two lines behave differently for the reason 2.2 gave: `run2["model"]["temperature"] = 0.9` changes an object that
    both dicts share, while `run2["tags"] = [...]` points one key of the new outer dict at a new list. Shallow copies protect
    you against **rebinding** at the top level, never against **changes inside** shared items."""),
    callout("sql", "SQL / Power BI", """A shallow copy is like a new table of **foreign keys** pointing at the same
    dimension rows: add a row to your copy and the original does not see it, but edit a dimension row and both tables see
    it. A deep copy also duplicates the dimension rows."""),
)

section("grids", "Building nested lists safely",
    p("""The multiplication operator repeats **references**. `[0] * 3` is fine because `0` is immutable. `[[0] * 3] * 3`
    repeats one inner list three times, so the "grid" has a single row shared three times. Build each inner object
    separately with a comprehension, so the inner expression runs once per row."""),
    ex("""
    bad = [[0] * 3] * 3
    bad[0][0] = 1
    print(bad)

    good = [[0] * 3 for _ in range(3)]
    good[0][0] = 1
    print(good)
    print(len({id(r) for r in bad}), len({id(r) for r in good}))
    """, "grids.py"),
)

section("deepcopy", "What deepcopy does for you, and what it costs",
    p("""`copy.deepcopy` walks the whole structure and keeps a **memo**: a dict from the id of each object it has
    already copied to its copy. That gives it two properties you rarely think about, but rely on:"""),
    p("""- **Shared objects stay shared inside the copy.** If two slots of the original point at one list, the two slots
      of the copy point at one (new) list. The structure is preserved, not just the values.
    - **Cycles work.** A list that contains itself is copied without looping forever."""),
    ex("""
    import copy

    shared = [0]
    data = {"a": shared, "b": shared}
    clone = copy.deepcopy(data)
    clone["a"].append(1)
    print(clone, data)
    print(clone["a"] is clone["b"], clone["a"] is data["a"])
    """, "deepcopy_memo.py"),
    p("""The costs: deepcopy is pure Python and visits every object, so it is slow on big data (problem 8). It cannot
    copy some objects at all, such as open files, network connections, locks and generators, and it copies objects you
    may have wanted to share, like a large read-only lookup table or a loaded model. Classes can control this with
    `__copy__` and `__deepcopy__` methods (Module 9)."""),
    ex("""
    import copy

    def numbers():
        yield 1

    for thing in [{"cfg": [1]}, numbers()]:
        try:
            print(copy.deepcopy(thing))
        except TypeError as e:
            print("TypeError:", e)
    """, "deepcopy_limits.py"),
    p("""A popular shortcut for "deep copy" of data that came from JSON is `json.loads(json.dumps(x))`. It does produce an
    independent copy, and it is sometimes faster than `deepcopy` for plain data, but it is **not** a faithful copy: it only works
    for JSON types, and it changes some of them on the way. Tuples come back as lists and integer dict keys come back as
    strings, which silently breaks code that looks up `d[1]` afterwards. Use it only when the data is JSON-shaped already."""),
    ex("""
    import copy, json

    data = {1: ("a", "b"), "scores": [0.5]}
    via_json = json.loads(json.dumps(data))
    print(via_json, copy.deepcopy(data) == data, via_json == data)
    """, "json_copy.py"),
)

section("avoid", "Often the best copy is no copy",
    p("""Copying is a defence against changes. Two designs need much less of it:"""),
    p("""- **Build new values instead of changing old ones.** `cfg | {"temperature": 0.9}`, `row + [1.0]`,
      `sorted(xs)` and comprehensions all build new objects and leave the input alone, so there is nothing to protect.
    - **Make shared data read-only.** Tuples, `frozenset` and `types.MappingProxyType` (a read-only view of a dict)
      cannot be changed, so they can be shared freely (problem 17).
    - **Copy only the path that changes.** To change one nested value, copy the dicts along the path to it and reuse
      every other branch. This is called **structural sharing**, and it is how immutable data libraries stay fast
      (problem 14)."""),
    p("""Structural sharing is easier to see than to describe. To change `cfg["model"]["temperature"]` without touching `cfg`,
    build a new outer dict and a new `model` dict, and let everything else (here the large `data` section) be shared by
    reference. Only the two dicts on the path to the change are new; nothing is deep-copied, and the original is untouched."""),
    ex("""
    cfg = {"model": {"name": "small", "temperature": 0.2}, "data": {"paths": ["a.jsonl", "b.jsonl"]}}

    new = {**cfg, "model": {**cfg["model"], "temperature": 0.9}}
    print(cfg["model"]["temperature"], new["model"]["temperature"])
    print(new["data"] is cfg["data"], new["model"] is cfg["model"])
    """, "structural_sharing.py"),
    p("""This only stays safe if nobody changes the shared branches in place later, which is why it pairs naturally with the
    "build new values" habit above. It is the style of React state updates, of Redux, and of libraries such as `pyrsistent`:
    every change produces a new version that shares most of its structure with the old one, which is cheap and makes the
    history of versions available for free."""),
    callout("note", "numpy and pandas", """`arr.copy()` copies a numeric numpy array completely. `df.copy()` (deep by
    default) copies the data and the index, but **not** Python objects stored inside an object column, such as lists in
    a `tags` column (problem 13). With pandas 3 Copy-on-Write (2.2) you rarely need `df.copy()` just to protect a DataFrame
    from changes made through a derived one."""),
)

section("warmup", "Warm-up",
    predict("A shallow copy of nested lists", "easy",
        code="""
        a = [[1, 2], [3]]
        b = a.copy()
        b.append([4])
        b[0].append(99)
        print(a)
        print(b)
        print(a is b, a[0] is b[0])
        """,
        hints=["`a.copy()` makes a new outer list. What do its first two slots point at?"],
        why="""`b.append([4])` changes only `b`'s outer list. `b[0]` is the very same inner list as `a[0]`, so appending
        99 shows in both. The outer lists are different objects, the inner ones are shared: that is the definition of a
        shallow copy."""),
    predict("Copying a nested config", "easy", tag="GenAI",
        code="""
        cfg = {"model": "small", "params": {"temperature": 0.2}}
        run = dict(cfg)
        run["model"] = "large"
        run["params"]["temperature"] = 0.9
        print(cfg)
        print(run)
        """,
        hints=["`dict(cfg)` copies one level. Which value in `cfg` is itself a mutable object?"],
        why="""`run["model"] = "large"` replaces a value in `run`'s own dict, so `cfg` keeps `"small"`. But
        `run["params"]` is the same inner dict as `cfg["params"]`, so changing the temperature through `run` changes it in
        `cfg` too. This is the classic "I copied the config and the original still changed" bug in experiment code."""),
    fix("A grid with one shared row", "easy", tag="Data work",
        prompt="""`make_grid(rows, cols)` should return a `rows` by `cols` grid of zeros where each cell can be set on its
        own. Setting one cell changes a whole column. Fix it.""",
        code="""
        def make_grid(rows, cols):
            return [[0] * cols] * rows
        """,
        tests="""
        g = make_grid(3, 2)
        g[0][1] = 5
        assert g == [[0, 5], [0, 0], [0, 0]]
        assert len({id(r) for r in make_grid(4, 4)}) == 4
        assert make_grid(0, 3) == []
        """,
        hints=["`* rows` repeats one inner list. Make the inner list once per row instead."],
        solution="""
        def make_grid(rows, cols):
            return [[0] * cols for _ in range(rows)]
        """,
        why="""In the comprehension, `[0] * cols` is evaluated once per row, so every row is its own list. `[0] * cols`
        itself is still fine, because the zeros are immutable ints: sharing them is harmless. The rule: multiplying a list
        is safe only when its items are immutable. For real numeric grids, `np.zeros((rows, cols))` avoids the question
        completely."""),
    write("Clone chat messages before editing", "easy", tag="GenAI",
        prompt="""Messages are flat dicts like `{"role": "user", "content": "..."}`. Write `clone_messages(messages)` that
        returns a list you can freely edit (append to it, change any message's content) without touching the original
        list or its messages. No `deepcopy`: the dicts are flat, so one level more than `list()` is enough.""",
        code="""
        def clone_messages(messages):
            pass
        """,
        tests="""
        orig = [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hi"}]
        c = clone_messages(orig)
        c[1]["content"] = "hello"
        c.append({"role": "user", "content": "more"})
        assert orig == [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hi"}]
        assert c[0] == orig[0] and c[0] is not orig[0]
        assert clone_messages([]) == []
        """,
        hints=["A new list, holding a new dict for each message: `dict(m)` copies a flat dict."],
        solution="""
        def clone_messages(messages):
            return [dict(m) for m in messages]
        """,
        why="""`list(messages)` would protect the list but share the message dicts (the leak from 2.2, problem 6).
        `[dict(m) for m in messages]` copies exactly two levels, which is all this data has, and is much faster than
        `deepcopy`. Copying exactly as deep as your data needs is the professional default; reach for `deepcopy` when the
        depth is unknown or varies."""),
)

section("medium", "Medium",
    predict("deepcopy keeps shared objects shared", "medium",
        code="""
        import copy

        shared = [0]
        data = {"a": shared, "b": shared}
        d1 = copy.copy(data)
        d2 = copy.deepcopy(data)
        d2["a"].append(1)
        print(data)
        print(d2)
        print(d2["a"] is d2["b"], d1["a"] is data["a"])
        """,
        hints=["deepcopy remembers each object it has already copied (the memo)."],
        why="""`copy.copy` is shallow: `d1["a"]` is still the original `shared` list. `deepcopy` copies `shared` once and
        reuses that copy for the second slot, because the memo says it has already been copied. So inside `d2` both keys
        still point at one list, and the append shows under both keys of `d2` but not in `data`. deepcopy preserves the
        **shape** of the sharing, not just the values."""),
    fix("Experiment variants that share settings", "medium", tag="ML",
        prompt="""This builds one config per temperature for an evaluation sweep. Every variant ends up with the last
        temperature. Fix `make_variants` so each variant is independent and `BASE` never changes.""",
        code="""
        BASE = {"model": "small", "params": {"temperature": 0.0, "max_tokens": 256}, "tags": ["sweep"]}

        def make_variants(temps):
            variants = []
            for t in temps:
                v = BASE.copy()
                v["params"]["temperature"] = t
                v["tags"].append(f"t={t}")
                variants.append(v)
            return variants
        """,
        tests="""
        vs = make_variants([0.0, 0.5, 1.0])
        assert [v["params"]["temperature"] for v in vs] == [0.0, 0.5, 1.0]
        assert [v["tags"] for v in vs] == [["sweep", "t=0.0"], ["sweep", "t=0.5"], ["sweep", "t=1.0"]]
        assert BASE == {"model": "small", "params": {"temperature": 0.0, "max_tokens": 256}, "tags": ["sweep"]}
        assert vs[0]["params"] is not vs[1]["params"]
        """,
        hints=["`BASE.copy()` is shallow. Which values inside `BASE` are mutable?",
               "`copy.deepcopy(BASE)` fixes it in one line. Can you also do it without deepcopy, by building new inner objects?"],
        solution="""
        import copy

        BASE = {"model": "small", "params": {"temperature": 0.0, "max_tokens": 256}, "tags": ["sweep"]}

        def make_variants(temps):
            variants = []
            for t in temps:
                v = copy.deepcopy(BASE)
                v["params"]["temperature"] = t
                v["tags"].append(f"t={t}")
                variants.append(v)
            return variants
        """,
        why="""Each `BASE.copy()` is a new outer dict, but `"params"` and `"tags"` are the same objects in every variant
        and in `BASE`, so every change lands in one shared dict and one shared list. `deepcopy` gives each variant its own.
        A version without deepcopy builds the inner objects fresh:
        `{**BASE, "params": {**BASE["params"], "temperature": t}, "tags": BASE["tags"] + [f"t={t}"]}`. It is faster and
        shows exactly what changes, but it must be updated whenever `BASE` gains another nested value."""),
    trace("Alias, slice and deepcopy side by side", "medium",
        prompt="Fill in `a`, `c` and `d` after each line. `c` is a shallow copy, `d` a deep copy.",
        code="""
        import copy
        a = [[1], [2]]
        c = a[:]
        d = copy.deepcopy(a)  # row: "after both copies"
        a[0].append(9)  # row: "a[0].append(9)"
        a.append([3])  # row: "a.append([3])"
        c[1] = [0]  # row: "c[1] = [0]"
        """,
        trace_vars=["a", "c", "d"],
        hints=["Changing an inner list shows wherever that inner list is shared. Changing a slot of an outer list does not."],
        why="""`a[0].append(9)` changes the inner list shared by `a` and `c`, but not `d`'s own copy. `a.append([3])`
        changes only `a`'s outer list. `c[1] = [0]` replaces a slot in `c`'s outer list, which `a` does not share. So
        there are two kinds of change: to an **inner** object, which is visible through every shallow copy, and to an
        **outer** slot, which is visible only through that container."""),
    choose("deepcopy or a JSON round trip?", "medium",
        prompt="""Both make an independent copy of 3,000 logged tool calls (nested dicts and lists of strings, numbers and
        booleans). Which is faster?""",
        setup="""import copy, json
doc = [{"tool": "search", "args": {"q": "refund", "k": 5, "filters": {"year": 2025, "tags": ["a", "b"]}}, "ok": True}
       for _ in range(3000)]""",
        options={
            "a": "clone = copy.deepcopy(doc)",
            "b": "clone = json.loads(json.dumps(doc))",
        },
        answer="b",
        hints=["`deepcopy` is written in Python and keeps a memo for every object. Where does the `json` module do its work?"],
        why="""`json.dumps` and `json.loads` run in C, while `deepcopy` runs Python code for every single object and records
        each one in its memo. In the timings above the round trip is faster, though not by a huge margin; the exact margin
        depends on the data's shape and the Python build, so measure on your own data. But it is only a copy
        **for JSON data**: tuples come back as lists, non-string dict keys become strings, and anything that is not JSON
        (dates, sets, custom objects) raises an error (problem 12). Use it when you know the data is pure JSON, such as a
        parsed API response."""),
    predict("Rows that are copies of shared rows", "medium",
        code="""
        a = [[]] * 3
        a[0].append("x")
        b = [[] for _ in range(3)]
        b[0].append("x")
        c = [list(row) for row in a]
        c[1].append("y")
        print(a)
        print(b)
        print(c)
        print(len({id(r) for r in a}), len({id(r) for r in c}))
        """,
        hints=["How many distinct inner lists does `a` have? `list(row)` makes a new list from whatever `row` contains."],
        why="""`a` has one inner list in three slots, so all three show `"x"`. `b` builds three separate lists. `c` copies
        each slot of `a`: it gets three **new** lists that each start with the contents of the shared list, `["x"]`. They
        are independent from then on, so only `c[1]` gets `"y"`. Copying fixes the aliasing going forward, but it copies
        whatever the shared object held at that moment."""),
    write("Merge layered settings", "medium", tag="GenAI",
        prompt="""Settings come in layers: defaults, then environment, then the user's choices. Write
        `merge_settings(base, override)` that returns a **new** dict: nested dicts are merged key by key (recursively),
        any other value in `override` replaces the one in `base`. Neither input may change, and the result must not share
        any nested dict with `base` that the merge touched.""",
        code="""
        def merge_settings(base, override):
            pass
        """,
        tests="""
        base = {"llm": {"model": "small", "params": {"temperature": 0.2, "top_p": 1.0}}, "k": 5}
        over = {"llm": {"params": {"temperature": 0.7}}, "k": 8, "debug": True}
        out = merge_settings(base, over)
        assert out == {"llm": {"model": "small", "params": {"temperature": 0.7, "top_p": 1.0}}, "k": 8, "debug": True}
        assert base == {"llm": {"model": "small", "params": {"temperature": 0.2, "top_p": 1.0}}, "k": 5}
        assert over == {"llm": {"params": {"temperature": 0.7}}, "k": 8, "debug": True}
        assert out["llm"] is not base["llm"] and out["llm"]["params"] is not base["llm"]["params"]
        assert merge_settings({"a": {"x": 1}}, {"a": 2}) == {"a": 2}
        """,
        hints=["Start with `out = dict(base)`. For each key in `override`: if both sides hold a dict, merge them by calling `merge_settings` again; otherwise take the override value.",
               "The recursive call returns a new dict, which is why the merged branches are not shared with `base`."],
        solution="""
        def merge_settings(base, override):
            out = dict(base)
            for key, value in override.items():
                if isinstance(out.get(key), dict) and isinstance(value, dict):
                    out[key] = merge_settings(out[key], value)
                else:
                    out[key] = value
            return out
        """,
        why="""`dict(base)` copies one level, and each recursive call copies the next level down **only along keys that
        are being merged**. Branches that the override does not touch stay shared with `base`, which is safe as long as
        nobody changes the result in place. The last test shows the type rule: a non-dict override replaces a whole
        dict. This is how configuration libraries (Hydra, Pydantic settings, Helm values files) layer settings, and
        `base | override` would be wrong here because it replaces `"llm"` entirely."""),
    refactor("Copy a table without hand-written loops", "medium",
        prompt="Make this shorter and clearer, keeping the same behaviour. Keep the tests green.",
        code="""
        def copy_table(table):
            new_table = []
            for row in table:
                new_row = []
                for cell in row:
                    new_row.append(cell)
                new_table.append(new_row)
            return new_table
        """,
        tests="""
        t = [[1, 2], [3, 4]]
        c = copy_table(t)
        c[0][0] = 99
        c.append([5])
        assert t == [[1, 2], [3, 4]]
        assert c == [[99, 2], [3, 4], [5]]
        assert copy_table([]) == []
        """,
        hints=["Each row needs its own new list; the cells are immutable numbers."],
        solution="""
        def copy_table(table):
            return [row[:] for row in table]
        """,
        why="""The original is a two-level copy written out by hand. `[row[:] for row in table]` (or `list(row)`) does the
        same: a new outer list and a new list per row, sharing only the immutable cells. It states the intent ("copy each
        row") in one line, and it is faster because slicing runs in C."""),
    predict("What a JSON round trip changes", "medium", tag="GenAI",
        code="""
        import json

        data = {"ids": (1, 2), 3: "three", "nested": {"x": [1]}}
        clone = json.loads(json.dumps(data))
        print(clone)
        print(clone == data)
        clone["nested"]["x"].append(2)
        print(data["nested"])
        """,
        hints=["JSON has arrays (lists) and objects with string keys only."],
        why="""JSON has no tuples, so `(1, 2)` comes back as `[1, 2]`, and JSON object keys are always strings, so the key
        `3` becomes `"3"`. The clone is therefore **not equal** to the original, even though it looks almost the same. It is
        fully independent, so the append does not touch `data`. Round-tripping through JSON is how a lot of LLM tool data
        travels anyway, so this is also the reason a cached or logged tool call can compare unequal to the live one."""),
)

section("hard", "Hard",
    predict("pandas: what `df.copy()` does not copy", "hard", tag="ML",
        code="""
        import pandas as pd

        df = pd.DataFrame({"id": [1, 2], "tags": [["a"], ["b"]]})
        c = df.copy()
        c.loc[0, "id"] = 100
        c.loc[0, "tags"] = "replaced"
        c["tags"].iloc[1].append("z")
        print(df["id"].tolist())
        print(df["tags"].tolist())
        print(c["tags"].tolist())
        """,
        hints=["`df.copy()` copies the column data. For an object column, the data is a list of references to Python objects.",
               "`.iloc[1]` here returns the list object stored in that cell, and `.append` changes that object."],
        why="""`c.loc[...] = ...` writes into `c`'s own copied columns, so `df` keeps its `id` and its first tag. But the
        `tags` column holds Python lists, and `df.copy()` copied the **references** to them, not the lists themselves.
        `c["tags"].iloc[1]` returns the shared list, and `.append("z")` changes it in place, so `df` sees `"z"` too. The
        pandas documentation says it directly: with `deep=True`, Python objects inside are not copied recursively. Lists
        or dicts inside DataFrame cells (common with LLM outputs and JSON columns) need `copy.deepcopy` of those cells, or
        better, never change them in place."""),
    write("Change one nested value, share the rest", "hard", tag="GenAI",
        prompt="""Write `with_override(config, path, value)` that returns a new config where the nested key at `path` (a
        tuple of keys) is set to `value`. Copy **only** the dicts along the path, and reuse every other branch as it is
        (structural sharing). Missing dicts along the path are created. The input must not change.""",
        code="""
        def with_override(config, path, value):
            pass
        """,
        tests="""
        base = {"llm": {"model": "small", "params": {"temperature": 0.2, "top_p": 1.0}}, "retriever": {"k": 5}}
        new = with_override(base, ("llm", "params", "temperature"), 0.9)
        assert new["llm"]["params"] == {"temperature": 0.9, "top_p": 1.0}
        assert base["llm"]["params"]["temperature"] == 0.2
        assert new["retriever"] is base["retriever"]
        assert new["llm"] is not base["llm"] and new["llm"]["params"] is not base["llm"]["params"]
        assert with_override({}, ("a", "b"), 1) == {"a": {"b": 1}}
        assert with_override(base, ("retriever",), None)["retriever"] is None
        """,
        hints=["One level at a time: copy the current dict, then set its key to the result of the same operation one level down.",
               "When `path` has one key left, that key simply gets `value`. Use `config.get(key, {})` for missing levels."],
        solution="""
        def with_override(config, path, value):
            key, rest = path[0], path[1:]
            new = dict(config)
            if rest:
                new[key] = with_override(config.get(key, {}), rest, value)
            else:
                new[key] = value
            return new
        """,
        why="""Each call copies exactly one dict, and only the dicts on the path get copied, so the cost depends on the
        depth, not the size of the config. Everything else is shared, which is safe because nothing is changed in place.
        This is structural sharing, the idea behind Redux-style state updates, Clojure's data structures and pyrsistent.
        Compared to `deepcopy` of a big config for each of 1,000 sweep variants, it is both faster and lighter on memory,
        and `new["retriever"] is base["retriever"]` proves nothing was copied needlessly."""),
    predict("deepcopy and a list that contains itself", "hard",
        code="""
        import copy

        a = [1]
        a.append(a)
        b = copy.deepcopy(a)
        print(a)
        print(b[1] is b, b[1] is a)
        print(len(b), b[1][1][1][0])
        """,
        hints=["`a.append(a)` puts the list inside itself. Python prints a reference to an outer list as `[...]`.",
               "The memo maps each original object to its copy. What is `a` mapped to when deepcopy meets `a` again inside itself?"],
        why="""`a` contains itself, so Python prints `[1, [...]]` rather than recursing forever. When `deepcopy` meets `a` a
        second time inside itself, the memo already maps `a` to the new list `b`, so it inserts `b` itself: the copy has the
        same cycle, pointing at itself and not at the original. Following the cycle any number of times stays inside `b`,
        so `b[1][1][1][0]` is still `1`. Without the memo, deepcopy would recurse until it crashed."""),
    fix("Read the code: prompt templates that drift", "hard", tag="GenAI",
        prompt="""A small prompt-template module. After a few requests, the templates themselves contain earlier users'
        questions, and the few-shot examples keep growing. Read the module, find the copying bugs, and fix them so the
        templates never change.""",
        code="""
        TEMPLATES = {
            "qa": {
                "messages": [
                    {"role": "system", "content": "Answer from the context only."},
                    {"role": "user", "content": "Context: {context}\\nQuestion: {question}"},
                ],
                "examples": [{"q": "What is RAG?", "a": "Retrieval-augmented generation."}],
            }
        }


        def build_prompt(name, context, question, extra_examples=()):
            template = TEMPLATES[name]
            messages = list(template["messages"])
            for m in messages:
                m["content"] = m["content"].format(context=context, question=question)
            examples = template["examples"]
            examples.extend(extra_examples)
            return {"messages": messages, "examples": examples}
        """,
        tests="""
        p1 = build_prompt("qa", "Refunds take 5 days.", "How long do refunds take?", [{"q": "Hi?", "a": "Hello."}])
        p2 = build_prompt("qa", "Shipping is free.", "Is shipping free?")
        assert p1["messages"][1]["content"].endswith("How long do refunds take?")
        assert p2["messages"][1]["content"] == "Context: Shipping is free.\\nQuestion: Is shipping free?"
        assert len(p1["examples"]) == 2 and len(p2["examples"]) == 1
        assert TEMPLATES["qa"]["messages"][1]["content"] == "Context: {context}\\nQuestion: {question}"
        assert len(TEMPLATES["qa"]["examples"]) == 1
        """,
        hints=["`list(template[\"messages\"])` copies the list but not the message dicts that the loop then changes.",
               "`examples = template[\"examples\"]` is not a copy at all.",
               "Build new message dicts, and a new examples list, instead of changing the template's objects."],
        solution="""
        TEMPLATES = {
            "qa": {
                "messages": [
                    {"role": "system", "content": "Answer from the context only."},
                    {"role": "user", "content": "Context: {context}\\nQuestion: {question}"},
                ],
                "examples": [{"q": "What is RAG?", "a": "Retrieval-augmented generation."}],
            }
        }


        def build_prompt(name, context, question, extra_examples=()):
            template = TEMPLATES[name]
            messages = [
                {**m, "content": m["content"].format(context=context, question=question)}
                for m in template["messages"]
            ]
            examples = template["examples"] + list(extra_examples)
            return {"messages": messages, "examples": examples}
        """,
        why="""Two different copying mistakes. `list(...)` is a shallow copy, so the loop rewrites the **template's** message
        dicts: after the first request, `{question}` is gone from the template and every later user gets the first user's
        question. And `examples = template["examples"]` is a plain alias, so `extend` grows the template's list on every
        request. The fix builds new objects instead of copying and then changing: a new dict per message with
        `{**m, "content": ...}`, and `template["examples"] + list(extra_examples)` for a new list. In a web server these
        bugs are worse than here, because one user's data leaks into other users' prompts. Treating templates as
        read-only data (tuples, `MappingProxyType`) would make Python raise instead."""),
    write("Freeze a config so nobody can change it", "hard", tag="GenAI",
        prompt="""Shared defaults keep getting changed by accident. Write `freeze_config(cfg)` that returns a read-only
        version at every depth: dicts become `types.MappingProxyType` views of new dicts, lists become tuples, other values
        stay as they are. Later changes to the original `cfg` must not show through.""",
        code="""
        from types import MappingProxyType

        def freeze_config(cfg):
            pass
        """,
        tests="""
        def raises(exc, f):
            try:
                f()
            except exc:
                return True
            return False
        cfg = {"model": "small", "params": {"temperature": 0.2}, "stops": ["###"]}
        fc = freeze_config(cfg)
        assert fc["params"]["temperature"] == 0.2 and fc["stops"] == ("###",)
        def set_top(): fc["model"] = "large"
        def set_nested(): fc["params"]["temperature"] = 0.9
        def add_stop(): fc["stops"].append("END")
        assert raises(TypeError, set_top)
        assert raises(TypeError, set_nested)
        assert raises(AttributeError, add_stop)
        cfg["params"]["temperature"] = 1.5
        assert fc["params"]["temperature"] == 0.2
        """,
        hints=["Recursion again: a dict becomes `MappingProxyType({k: freeze_config(v) for ...})`, a list becomes a tuple of frozen items.",
               "Building **new** inner dicts is what stops later changes to `cfg` showing through."],
        solution="""
        from types import MappingProxyType

        def freeze_config(cfg):
            if isinstance(cfg, dict):
                return MappingProxyType({k: freeze_config(v) for k, v in cfg.items()})
            if isinstance(cfg, list):
                return tuple(freeze_config(v) for v in cfg)
            return cfg
        """,
        why="""`MappingProxyType` is a read-only window onto a dict: reading works, and assigning raises `TypeError`. A
        window onto the **original** dict would still show changes made to that dict, so the function builds a new dict at
        every level and only then wraps it. Lists become tuples, which have no `append` at all. The result can be passed
        around freely: there is nothing left to copy defensively. Pydantic's `frozen=True` models and frozen dataclasses
        (Module 11) give the same guarantee for typed configs."""),
)

section("interview", "Interview questions",
    explain("What is the difference between a shallow and a deep copy, and when do you need each?", "medium", tag="Interview",
        why="""A shallow copy creates a new outer container but fills it with references to the same inner objects
        (`list(x)`, `x[:]`, `dict.copy()`, `copy.copy`). A deep copy (`copy.deepcopy`) recursively copies the inner objects
        too, using a memo so shared references and cycles are preserved. Shallow is enough when the contents are immutable,
        or when you will only change the outer container. Deep is needed when you will change nested mutable objects and
        must not affect the original. Mention the costs of deepcopy (slow, cannot copy files, locks, connections, copies
        large shared objects needlessly), the cheaper alternatives (copy exactly as deep as the data, build new values
        instead of changing old ones, read-only structures), and the pandas detail that `df.copy()` does not copy Python
        objects inside object columns."""),
    explain("You need 1,000 variants of a large nested config, each changing a few values. How do you build them efficiently?", "hard", tag="Interview",
        why="""Deep-copying the whole config 1,000 times works but costs time and memory proportional to the full size each
        time. Better: structural sharing. Copy only the dicts along the path you change and reuse untouched branches, which
        makes each variant cost proportional to the depth of the change. This is safe only if nobody changes configs in place,
        so make them read-only (`MappingProxyType`, frozen dataclasses or Pydantic models) or agree that configs are
        treated as immutable values. If the variants come from a grid of options, generate them lazily with
        `itertools.product` and build each one only when a run starts, so 1,000 configs never sit in memory at once.
        Hyperparameter sweep tools also create each trial's settings when the trial starts, for the same reason."""),
    explain("Does `df.copy()` give you a completely independent DataFrame?", "hard", tag="Interview",
        why="""Mostly. `df.copy()` defaults to `deep=True`, which copies the underlying data arrays and the index, so writes
        to the copy's columns do not affect the original. But for **object** columns, the copied array holds references to
        the same Python objects: lists, dicts or custom objects in the cells are shared, so changing one of them in place
        through the copy changes the original as well. The pandas docs state that Python objects are not copied
        recursively. `copy.deepcopy(df)` does not fully solve this either, because pandas implements it as `df.copy(deep=True)`.
        You would apply `copy.deepcopy` to those cells yourself. Also mention that with pandas 3 Copy-on-Write you rarely need
        `df.copy()` to protect against changes through a derived DataFrame, since that can no longer happen."""),
)

recap(
    "`b = a` is no copy. Shallow copies (`list(a)`, `a[:]`, `dict(d)`, `copy.copy`) duplicate one level. `copy.deepcopy` duplicates every level.",
    "A shallow copy is enough when the contents are immutable. Nested mutable data (configs, messages, JSON) needs a deeper copy or a different design.",
    "Multiplying a list repeats references: `[[0] * 3] * 3` is one row three times. Build nested lists with a comprehension.",
    "deepcopy keeps shared objects shared and handles cycles, but it is slow and copies everything. Copy exactly as deep as the data needs.",
    "Often the best copy is none: build new values, share read-only data, and copy only the path that changes. `df.copy()` does not copy Python objects inside cells.",
)
