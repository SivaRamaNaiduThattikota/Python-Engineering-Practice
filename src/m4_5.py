from lesson import *

lesson(
    id="m4-5", num="4.5", title="Dicts: the basics",
    intro="A dict maps keys to values with O(1) lookups and keeps insertion order. How to read values safely, why views "
          "are live and why you cannot change a dict while looping over it, merging with clear precedence, and the hash "
          "join: the SQL join you can write in four lines.",
    desc="Keys, `get`, iteration, insertion order, merging and updating.",
    keys="dict mapping key value hash table get keyerror in setdefault items keys values views insertion order update merge | |= comprehension zip invert nested get runtimeerror changed size hash join",
)

term("dict", "A mapping from hashable keys to values, stored in a hash table: lookup, insert and delete by key are O(1) on average.")
term("View", "`d.keys()`, `d.values()` and `d.items()`: live windows onto a dict that reflect later changes without copying.")
term("Insertion order", "Since Python 3.7 a dict remembers the order keys were first inserted, and iterates in that order.")
term("Hash join", "Joining two tables by building a dict on one side's key, then looking each row of the other side up in it: O(n + m).")

section("what", "What a dict is",
    p("""A dict maps **keys** to **values**. Under the hood it is a hash table, like a set (4.4), where each key's slot also
    stores its value. So `d[key]`, `d[key] = value`, `del d[key]` and `key in d` are all **O(1) on average**, however
    many items the dict holds. Keys must be hashable (strings, numbers, tuples of those, frozensets); values can be
    anything at all, including lists and other dicts."""),
    p("""Since Python 3.7 dicts also **keep insertion order**: iterating gives keys in the order they were first added.
    CPython achieves this with a "compact" layout: a small hash index points into a separate array of entries stored in
    insertion order, which also uses less memory than the old design. Assigning a new value to an existing key keeps its
    position; deleting a key and adding it again moves it to the end."""),
    ex("""
    prices = {"basic": 0, "pro": 20, "team": 50}
    print(prices["pro"], "team" in prices, 20 in prices, len(prices))   # `in` checks keys, not values
    prices["enterprise"] = 200          # new key: goes at the end
    prices["basic"] = 5                 # existing key: same position
    del prices["pro"]
    prices["pro"] = 25                  # re-added: now at the end
    print(list(prices))
    """, "dict_basics.py"),
    callout("sql", "SQL / Power BI", """A dict is a lookup table with a **primary key**: `prices["pro"]` is
    `SELECT price FROM prices WHERE plan = 'pro'` against an indexed key, and a missing key is "no row". In Power BI it is
    the dimension side of a relationship: you look up attributes by the key, and the key must be unique, which a dict
    guarantees (a repeated key overwrites)."""),
)

section("reading", "Reading values safely",
    p("""There are four ways to read, and choosing well is most of writing robust dict code:"""),
    html("""<div class="tbl"><table>
      <tr><th>Expression</th><th>Missing key</th><th>Use when</th></tr>
      <tr><td><code>d[k]</code></td><td>raises <code>KeyError</code></td><td>the key must be there; a missing key is a bug</td></tr>
      <tr><td><code>d.get(k)</code> / <code>d.get(k, default)</code></td><td>returns <code>None</code> / <code>default</code></td><td>the key is optional</td></tr>
      <tr><td><code>k in d</code></td><td><code>False</code></td><td>you only need to know if it exists</td></tr>
      <tr><td><code>d.setdefault(k, default)</code></td><td>inserts <code>default</code> and returns it</td><td>read, creating the entry if needed (4.6)</td></tr>
    </table></div>"""),
    ex("""
    cfg = {"model": "small", "timeout": 0, "stop": None}
    print(cfg.get("timeout", 30), cfg.get("retries", 3))   # 0 is a real value and is kept
    print(cfg.get("stop", ["###"]), "stop" in cfg)        # the key exists, with value None
    try:
        cfg["retries"]
    except KeyError as e:
        print("KeyError:", e)
    print(cfg.get("retries") is None, (cfg.get("timeout") or 30))  # `or` throws away the 0
    """, "reading.py"),
    p("""Two subtleties. `d.get(k, default)` returns the default only when the key is **absent**; if the key is present
    with the value `None`, you get `None`. When "absent" and "present but None" must be distinguished, use `k in d` or a
    sentinel default (2.1). And never write `d.get(k) or default` for values that can legitimately be `0`, `""` or `[]`:
    `or` replaces them too (1.1)."""),
    p("""For **nested** JSON, chained `get` calls with `{}` defaults avoid a crash at each level:
    `resp.get("usage", {}).get("total_tokens", 0)`. That works for one or two levels; for deep paths, write a helper
    (problem 6)."""),
)

section("iterating", "Iterating, and changing a dict safely",
    p("""Looping over a dict gives its **keys**. `d.items()` gives `(key, value)` pairs, which you unpack in the loop header
    (4.3), and `d.values()` gives the values. These three are **views**: live windows onto the dict, not copies. They are
    cheap, they reflect later changes, and `keys()` and `items()` support set operations (4.4)."""),
    ex("""
    counts = {"refund": 3, "login": 0, "invoice": 7}
    keys = counts.keys()
    counts["shipping"] = 2
    print(list(keys))                          # the view sees the new key
    for word, n in counts.items():
        print(f"{word}:{n}", end=" ")
    print()
    print(sum(counts.values()), sorted(counts.keys() - {"login"}))
    """, "views.py"),
    p("""Because a view is live, you **cannot add or remove keys while iterating** over a dict or its views: Python detects
    the size change and raises `RuntimeError: dictionary changed size during iteration`. Changing the **value** of an
    existing key is fine. To delete while looping, loop over a snapshot (`list(d)`), or better, build a new dict with a
    comprehension."""),
    ex("""
    vocab = {"the": 120, "refund": 9, "xqzt": 1, "a": 95, "tyop": 1}
    try:
        for word, n in vocab.items():
            if n < 2:
                del vocab[word]
    except RuntimeError as e:
        print("RuntimeError:", e)

    vocab = {"the": 120, "refund": 9, "xqzt": 1, "a": 95, "tyop": 1}
    kept = {w: n for w, n in vocab.items() if n >= 2}        # a new dict
    for word in list(vocab):                                  # or: loop over a snapshot
        if vocab[word] < 2:
            del vocab[word]
    print(kept == vocab, list(kept))
    """, "change_while_iterating.py"),
)

section("merging", "Merging and updating",
    p("""All the ways of combining dicts follow one rule: **for a repeated key, the later value wins**. They differ in
    whether they build a new dict or change an existing one:"""),
    p("""- **New dict:** `a | b` (Python 3.9+), `{**a, **b}`, `dict(a, **b)` (only for string keys).
    - **Change `a` in place:** `a |= b` or `a.update(b)`. `update` also accepts keyword arguments and lists of pairs."""),
    ex("""
    defaults = {"model": "small", "temperature": 0.2, "stop": ["###"]}
    env = {"model": "medium"}
    user = {"temperature": 0.9}
    merged = defaults | env | user                 # later wins: user over env over defaults
    print(merged)
    print(merged["stop"] is defaults["stop"])      # shallow: nested values are shared (2.3)
    defaults.update(max_tokens=512)
    print(list(defaults))
    """, "merging.py"),
    p("""Write the layers from **lowest to highest priority**, left to right, and the precedence reads naturally. Getting the
    order backwards (`overrides | defaults`) silently makes the defaults win, a bug that produces no error (problem 10).
    Every one of these merges is shallow: nested dicts and lists are shared, so use a recursive merge for nested settings
    (2.3, `merge_settings`)."""),
)

section("building", "Building and reshaping dicts",
    p("""Common ways to build a dict: a literal, `dict(zip(keys, values))` for two parallel lists, `dict(pairs)` for a list
    of `(key, value)` pairs, and a comprehension `{k: f(k) for k in items}` when you compute values. Two reshaping patterns
    come up constantly:"""),
    ex("""
    classes = ["eggs", "ham", "spam"]
    label_to_id = {label: i for i, label in enumerate(classes)}
    id_to_label = dict(enumerate(classes))
    print(label_to_id, id_to_label)

    scores = {"faq": 0.71, "guide": 0.93, "terms": 0.12}
    by_score = dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))
    print(by_score, next(iter(by_score)))

    owners = {"faq": "ana", "guide": "ben", "terms": "ana"}
    inverted = {owner: doc for doc, owner in owners.items()}   # duplicates: the last one wins
    print(inverted)
    """, "building.py"),
    p("""**Inverting** a dict (values become keys) silently loses entries when values repeat: `"ana"` owns two documents but
    the inverted dict keeps only the last. When values can repeat, invert into lists (`{owner: [docs]}`, 4.6), or check
    for duplicates and raise (problem 2). **Sorting** a dict means building a new dict from sorted items: the dict itself has
    no sort method, but it keeps whatever insertion order you build it with."""),
    callout("note", "Equality ignores order", """Two dicts are equal when they have the same keys with equal values, in any
    order: `{"a": 1, "b": 2} == {"b": 2, "a": 1}` is `True`. So insertion order affects iteration and printing, never
    equality. (`collections.OrderedDict` is the exception: comparing two OrderedDicts also compares order.)"""),
)

section("warmup", "Warm-up",
    predict("Square brackets, get and in", "easy",
        code="""
        resp = {"model": "small", "usage": {"prompt_tokens": 12, "completion_tokens": 0}, "error": None}
        print(resp["model"], resp.get("id"), resp.get("id", "n/a"))
        print("error" in resp, resp.get("error", "none"), resp["usage"]["completion_tokens"] or "empty")
        print(resp.get("usage", {}).get("total_tokens", 0))
        try:
            resp["choices"][0]
        except KeyError as e:
            print("KeyError:", e)
        """,
        hints=["`get` returns the default only when the key is absent, not when its value is `None`.",
               "`or` treats 0 as false."],
        why="""`get` with no default returns `None` for an absent key, and the given default otherwise. `"error"` is present with
        value `None`, so `get("error", "none")` returns `None`, not `"none"`. `0 or "empty"` gives `"empty"`, which would be a
        bug if 0 completion tokens were meaningful. The chained `get` returns 0 because `total_tokens` is absent. Indexing a
        missing key raises `KeyError` naming the key."""),
    write("Invert a label map, refusing duplicates", "easy", tag="ML",
        prompt="""Write `invert(mapping)` that turns `{label: id}` into `{id: label}`, and raises `ValueError` naming the
        repeated id if two labels share an id (inverting would silently lose one).""",
        code="""
        def invert(mapping):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc as e:
                return str(e)
            return False
        assert invert({"ham": 0, "spam": 1}) == {0: "ham", 1: "spam"}
        assert invert({}) == {}
        msg = raises(ValueError, invert, {"ham": 0, "spam": 1, "eggs": 0})
        assert msg and "0" in msg
        """,
        hints=["Build the result in a loop; before storing `out[value] = key`, check whether `value` is already a key of `out`."],
        solution="""
        def invert(mapping):
            out = {}
            for key, value in mapping.items():
                if value in out:
                    raise ValueError(f"id {value!r} is used by both {out[value]!r} and {key!r}")
                out[value] = key
            return out
        """,
        why="""A comprehension `{v: k for k, v in mapping.items()}` would be shorter, but it silently keeps only the last label for
        a repeated id, which in a label map means one class disappears from decoded predictions. Checking `value in out` is O(1)
        per item, so the safe version is still O(n). The error message names both labels, which is what you need to fix the
        data."""),
    fix("Optional settings that crash", "easy", tag="GenAI",
        prompt="""`client_settings(cfg)` builds settings for an LLM client. Configs that leave out `timeout` or `retries`
        crash. Missing values should default to `timeout=30` and `retries=3`, but a `timeout` of `0` (no timeout) must be kept.""",
        code="""
        def client_settings(cfg):
            return {"timeout": cfg["timeout"], "retries": cfg["retries"]}
        """,
        tests="""
        assert client_settings({}) == {"timeout": 30, "retries": 3}
        assert client_settings({"timeout": 0}) == {"timeout": 0, "retries": 3}
        assert client_settings({"timeout": 5, "retries": 0}) == {"timeout": 5, "retries": 0}
        """,
        hints=["`get` with a default handles absent keys. Do not use `or`, or the 0s disappear."],
        solution="""
        def client_settings(cfg):
            return {"timeout": cfg.get("timeout", 30), "retries": cfg.get("retries", 3)}
        """,
        why="""`cfg["timeout"]` treats a missing key as an error, but these settings are optional, so `get` with the documented
        default is the right tool. The tempting `cfg.get("timeout") or 30` would turn `timeout=0` and `retries=0` into the
        defaults, overriding an explicit choice (1.1, the COALESCE trap)."""),
    predict("Views are live", "easy",
        code="""
        stock = {"apple": 3, "pear": 0}
        ks = stock.keys()
        vs = stock.values()
        items = stock.items()
        stock["plum"] = 5
        stock["apple"] = 9
        print(list(ks), list(vs))
        print(("apple", 9) in items, len(items))
        print(ks & {"pear", "kiwi"}, type(ks).__name__)
        """,
        hints=["A view does not copy anything; it reads the dict each time you use it."],
        why="""The views were created before the changes, but they show the current dict: the new key `"plum"` and the new value
        for `"apple"` both appear. `items()` supports `in` with a `(key, value)` pair, and `keys()` supports set operations
        directly. If you need a snapshot that will not change, copy it: `list(d)`, `dict(d)` or `list(d.items())`."""),
)

section("medium", "Medium",
    fix("Pruning a vocabulary while looping over it", "medium", tag="ML",
        prompt="""`prune(vocab, min_count)` should remove rare words from the vocabulary dict **in place**. It raises
        `RuntimeError`. Fix it, keeping it in place (the same dict object).""",
        code="""
        def prune(vocab, min_count):
            for word, count in vocab.items():
                if count < min_count:
                    del vocab[word]
        """,
        tests="""
        v = {"the": 120, "refund": 9, "xqzt": 1, "a": 95, "tyop": 1}
        ref = v
        prune(v, 2)
        assert v == {"the": 120, "refund": 9, "a": 95} and v is ref
        prune(v, 1000)
        assert v == {}
        """,
        hints=["You cannot delete keys while iterating over the dict itself. Collect the keys to delete first, or loop over a copy of the keys."],
        solution="""
        def prune(vocab, min_count):
            for word in [w for w, c in vocab.items() if c < min_count]:
                del vocab[word]
        """,
        why="""Deleting during iteration changes the dict's size under the running iterator, which Python refuses to continue
        with. Building the list of rare words first finishes the iteration before any deletion starts. If the function did not
        have to work in place, `{w: c for w, c in vocab.items() if c >= min_count}` would be the clearest version. Pruning rare
        tokens is a standard step when building a vocabulary for bag-of-words features (scikit-learn's `min_df`)."""),
    write("Get a value deep inside JSON", "medium", tag="GenAI",
        prompt="""Write `dig(data, path, default=None)` that follows `path`, a list of keys and list positions, through nested
        dicts and lists, and returns `default` as soon as any step is missing (a missing key, a position out of range, or a
        value that is not a container).""",
        code="""
        def dig(data, path, default=None):
            pass
        """,
        tests="""
        resp = {"choices": [{"message": {"content": "Hi", "tool_calls": []}}], "usage": {"total_tokens": 42}}
        assert dig(resp, ["choices", 0, "message", "content"]) == "Hi"
        assert dig(resp, ["usage", "total_tokens"]) == 42
        assert dig(resp, ["choices", 1, "message"], "none") == "none"
        assert dig(resp, ["choices", 0, "message", "tool_calls", 0, "name"]) is None
        assert dig(resp, ["usage", "total_tokens", "x"], -1) == -1
        assert dig(resp, []) is resp
        """,
        hints=["Walk the path one step at a time. For each step, the current value must be a dict containing the key, or a list where the position is in range."],
        solution="""
        def dig(data, path, default=None):
            current = data
            for step in path:
                if isinstance(current, dict) and step in current:
                    current = current[step]
                elif isinstance(current, list) and isinstance(step, int) and -len(current) <= step < len(current):
                    current = current[step]
                else:
                    return default
            return current
        """,
        why="""LLM API responses are deeply nested and their shape varies (a refusal has no `tool_calls`, an error has no
        `choices`), so a single helper beats a pyramid of `if "choices" in resp and resp["choices"] and ...`. Checking before
        stepping (look before you leap) keeps the logic explicit; the other style, `try: ... except (KeyError, IndexError,
        TypeError): return default`, is shorter but can hide a real bug inside a step (Module 8 compares the two). The path as
        a list also makes the lookup easy to log when it fails."""),
    trace("Dict order, step by step", "medium",
        prompt="Fill in `list(d)` (the key order) and `d.get(\"b\")` after each marked line.",
        code="""
        d = {"b": 1}
        d["a"] = 2  # row: "d['a'] = 2"
        d["b"] = 3  # row: "d['b'] = 3"
        del d["b"]  # row: "del d['b']"
        d["b"] = 4  # row: "d['b'] = 4"
        d |= {"a": 0, "c": 5}  # row: "d |= {...}"
        """,
        trace_vars=["list(d)", "d.get(\"b\")"],
        hints=["Updating an existing key keeps its place. Deleting and re-adding moves it to the end."],
        why="""Adding `"a"` appends it after `"b"`. Updating `"b"` keeps its first position. Deleting `"b"` and adding it again
        puts it at the **end**. `|=` updates `"a"` in place (same position, new value 0) and appends the new key `"c"`. Insertion
        order is about when a key **first** entered the dict, which matters whenever dict order ends up in output: JSON, CSV
        headers, prompts."""),
    choose("Lookups in a list of pairs or a dict", "medium",
        prompt="Both look up the price for 5,000 product codes among 20,000 products. Which is faster?",
        setup="""pairs = [(f"p{i}", i * 1.5) for i in range(20_000)]
queries = [f"p{i}" for i in range(0, 20_000, 4)]
table = dict(pairs)
def find(code):
    for c, price in pairs:
        if c == code:
            return price""",
        options={
            "a": "prices = [find(q) for q in queries]",
            "b": "prices = [table[q] for q in queries]",
        },
        answer="b",
        hints=["How many pairs does `find` look at, on average, per query?"],
        why="""`find` scans the list of pairs until it hits the code: about half the list per query, so roughly 5,000 × 10,000
        comparisons. The dict computes each key's slot directly: 5,000 O(1) lookups. Building `table` costs one pass, which is
        paid back after a handful of lookups. "A list of `(key, value)` pairs that I search" is almost always a dict waiting to
        be written."""),
    write("Label maps that are stable", "medium", tag="ML",
        prompt="""Write `label_maps(labels)` that takes any iterable of class labels (with repeats) and returns
        `(label_to_id, id_to_label)`, numbering the distinct labels in **sorted** order from 0.""",
        code="""
        def label_maps(labels):
            pass
        """,
        tests="""
        l2i, i2l = label_maps(["spam", "ham", "spam", "eggs"])
        assert l2i == {"eggs": 0, "ham": 1, "spam": 2}
        assert i2l == {0: "eggs", 1: "ham", 2: "spam"}
        assert all(i2l[l2i[x]] == x for x in l2i)
        assert label_maps([]) == ({}, {})
        """,
        hints=["`classes = sorted(set(labels))` (4.4), then build both dicts from `enumerate(classes)`."],
        solution="""
        def label_maps(labels):
            classes = sorted(set(labels))
            label_to_id = {label: i for i, label in enumerate(classes)}
            id_to_label = dict(enumerate(classes))
            return label_to_id, id_to_label
        """,
        why="""Sorting makes the numbering deterministic across runs (4.4, problem 6), and building both directions from the same
        `classes` list guarantees they are exact inverses, which the third test checks. `dict(enumerate(classes))` is the
        shortest way to build "position to item". Save `classes` (or `id_to_label`) with the model; it is the only way to decode
        predictions back to names later."""),
    fix("Defaults that override the user", "medium", tag="GenAI",
        prompt="""`effective_config(defaults, user)` should return the user's settings on top of the defaults. Users report
        that their temperature is ignored. Fix the precedence, and make sure neither input dict is changed.""",
        code="""
        def effective_config(defaults, user):
            cfg = user
            cfg.update(defaults)
            return cfg
        """,
        tests="""
        d = {"model": "small", "temperature": 0.2}
        u = {"temperature": 0.9, "stop": ["###"]}
        out = effective_config(d, u)
        assert out == {"model": "small", "temperature": 0.9, "stop": ["###"]}
        assert d == {"model": "small", "temperature": 0.2}
        assert u == {"temperature": 0.9, "stop": ["###"]}
        assert out is not d and out is not u
        """,
        hints=["Two bugs: `update` lets the **argument** win, and `cfg = user` is an alias, not a copy."],
        solution="""
        def effective_config(defaults, user):
            return defaults | user
        """,
        why="""`cfg.update(defaults)` writes every default over the user's values, so the defaults win: precedence backwards. And
        `cfg = user` is an alias (2.2), so the user's own dict is changed too. `defaults | user` fixes both: it builds a new dict,
        and the right-hand side wins. Read merges left to right as "start from this, then apply that"."""),
    refactor("An if chain that is really a lookup", "medium",
        prompt="Replace the chain with a dict lookup, keeping exactly the same results, including the fallback. Keep the tests green.",
        code="""
        def region_name(code):
            if code == "eu":
                return "Europe"
            elif code == "us":
                return "United States"
            elif code == "apac":
                return "Asia-Pacific"
            elif code == "latam":
                return "Latin America"
            else:
                return "Unknown"
        """,
        tests="""
        assert [region_name(c) for c in ["eu", "us", "apac", "latam"]] == ["Europe", "United States", "Asia-Pacific", "Latin America"]
        assert region_name("mars") == "Unknown" and region_name("EU") == "Unknown"
        """,
        hints=["A module-level dict, and `get` with the fallback as default."],
        solution="""
        REGIONS = {"eu": "Europe", "us": "United States", "apac": "Asia-Pacific", "latam": "Latin America"}

        def region_name(code):
            return REGIONS.get(code, "Unknown")
        """,
        why="""The chain encoded a table as control flow; the dict states it as data, which can be extended, tested, loaded from a
        file or a database, and shown in a dropdown. `get` with a default replaces the `else`. This is the same refactor as the
        dispatch table in 3.5, with values instead of functions."""),
    predict("Equality, order and duplicate keys", "medium",
        code="""
        from collections import OrderedDict

        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        print(a == b, list(a) == list(b))
        print(OrderedDict(a) == OrderedDict(b), OrderedDict(a) == b)
        print({"k": 1, "k": 2}, dict([("k", 1), ("k", 2)]))
        print({1: "int", 1.0: "float", True: "bool"})
        """,
        hints=["Plain dict equality ignores order. A repeated key keeps its first position and its last value.",
               "Two OrderedDicts compare order; an OrderedDict compared with a plain dict does not."],
        why="""`a == b` is `True` although their key orders differ. Two `OrderedDict`s with different orders are **not** equal, but an
        `OrderedDict` compared with a plain dict ignores order. A repeated key in a literal or a list of pairs keeps the
        **first** position and the **last** value. `1`, `1.0` and `True` are the same key (4.4), so the dict has one entry: the
        key object stays `1` (the first one inserted) and the value is the last one written, `"bool"`."""),
)

section("hard", "Hard",
    write("Top-k entries of a dict", "hard", tag="RAG",
        prompt="""Write `top_k(scores, k)` that returns a **new dict** of the `k` entries with the highest values, ordered from
        highest to lowest, breaking ties by key ascending. Use `heapq.nlargest` (4.2) so a large dict is not fully sorted.""",
        code="""
        import heapq

        def top_k(scores, k):
            pass
        """,
        tests="""
        s = {"faq": 0.71, "guide": 0.93, "terms": 0.12, "blog": 0.93, "api": 0.5}
        assert list(top_k(s, 3).items()) == [("blog", 0.93), ("guide", 0.93), ("faq", 0.71)]
        assert top_k(s, 0) == {} and len(top_k(s, 10)) == 5
        assert top_k({}, 2) == {}
        """,
        hints=["`heapq.nlargest(k, scores.items(), key=...)` returns pairs. The key must rank higher values first and, for equal values, smaller keys first.",
               "A key of `(value, negated key)` is not possible for strings. `nsmallest` with `(-value, key)` is."],
        solution="""
        import heapq

        def top_k(scores, k):
            best = heapq.nsmallest(k, scores.items(), key=lambda kv: (-kv[1], kv[0]))
            return dict(best)
        """,
        why="""Strings cannot be negated, so "value descending, key ascending" is expressed as the **smallest** `(-value, key)`
        tuples, which `nsmallest` returns already in that order. Building a dict from the ordered pairs keeps that order, so the
        result reads highest first. `nsmallest(0, ...)` is an empty list, so `k = 0` needs no special case (unlike the `-0`
        slice trap, 4.1). Retrieval code does this after scoring chunks: keep the top few, in a deterministic order."""),
    fix("Read the code: token accounting with three bugs", "hard", tag="GenAI",
        prompt="""This module tracks token usage per user per model for billing. Usage for new models is lost, the monthly
        report crashes, and cleaning up zero entries raises `RuntimeError`. Read the module, find the three bugs, and fix
        them.""",
        code="""
        def record(usage, user, model, tokens):
            per_user = usage.get(user, {})
            per_user[model] = per_user.get(model, 0) + tokens


        def report(usage):
            lines = []
            for user in sorted(usage):
                total = sum(usage[user].values())
                top = max(usage[user], key=usage[user].get)
                lines.append(f"{user}: {total} tokens, mostly {top}")
            return lines


        def drop_unused(usage):
            for user, per_model in usage.items():
                if sum(per_model.values()) == 0:
                    del usage[user]
        """,
        tests="""
        usage = {}
        record(usage, "ana", "small", 120)
        record(usage, "ana", "large", 300)
        record(usage, "ana", "small", 30)
        record(usage, "ben", "small", 0)
        assert usage == {"ana": {"small": 150, "large": 300}, "ben": {"small": 0}}
        assert report(usage) == ["ana: 450 tokens, mostly large", "ben: 0 tokens, mostly small"]
        usage["cy"] = {}
        assert report(usage)[-1] == "cy: 0 tokens, mostly none"
        drop_unused(usage)
        assert usage == {"ana": {"small": 150, "large": 300}}
        """,
        hints=["`usage.get(user, {})` returns a **new** empty dict for a new user, which is never stored in `usage`. `setdefault` stores it.",
               "`max` of an empty dict raises. Give it a `default`.",
               "`drop_unused` deletes while iterating over `usage.items()`."],
        solution="""
        def record(usage, user, model, tokens):
            per_user = usage.setdefault(user, {})
            per_user[model] = per_user.get(model, 0) + tokens


        def report(usage):
            lines = []
            for user in sorted(usage):
                total = sum(usage[user].values())
                top = max(usage[user], key=usage[user].get, default="none")
                lines.append(f"{user}: {total} tokens, mostly {top}")
            return lines


        def drop_unused(usage):
            for user in [u for u, per_model in usage.items() if sum(per_model.values()) == 0]:
                del usage[user]
        """,
        why="""Bug one: `get(user, {})` returns a fresh dict that is never put **into** `usage`, so all usage of a new user (and
        each later call) vanishes; `setdefault(user, {})` returns the existing inner dict or stores and returns a new one, which
        is exactly "get or create" (4.6). Bug two: `max` over a user with no models raises `ValueError`; `default=` handles it.
        Bug three: deleting during iteration over `items()` raises `RuntimeError`; collect the users first. Billing code is
        where "silently lost" is the worst kind of bug, which is why the first one matters most."""),
    write("A hash join of two tables", "hard", tag="Interview",
        prompt="""Write `inner_join(left, right, key)` for two lists of dicts: return a list of merged dicts (right's fields
        added to left's) for every pair with equal values of `key`, in the order of `left`, and for duplicate matches in the
        order of `right`. It must run in O(len(left) + len(right) + output), so build a dict index on `right` first. Rows
        without the key are skipped.""",
        code="""
        def inner_join(left, right, key):
            pass
        """,
        tests="""
        orders = [{"order": 1, "cust": "c1"}, {"order": 2, "cust": "c9"}, {"order": 3, "cust": "c2"}, {"order": 4}]
        customers = [{"cust": "c1", "name": "Ana"}, {"cust": "c2", "name": "Ben"}, {"cust": "c1", "name": "Ana (old)"}]
        out = inner_join(orders, customers, "cust")
        assert out == [{"order": 1, "cust": "c1", "name": "Ana"}, {"order": 1, "cust": "c1", "name": "Ana (old)"},
                       {"order": 3, "cust": "c2", "name": "Ben"}]
        assert orders[0] == {"order": 1, "cust": "c1"}
        assert inner_join([], customers, "cust") == []
        """,
        hints=["Index the right side: a dict from key value to the **list** of right rows with that value (`setdefault(value, []).append(row)`).",
               "Then for each left row, look up its key and emit `{**left_row, **right_row}` for each match."],
        solution="""
        def inner_join(left, right, key):
            index = {}
            for row in right:
                if key in row:
                    index.setdefault(row[key], []).append(row)
            out = []
            for row in left:
                for match in index.get(row.get(key), []) if key in row else []:
                    out.append({**row, **match})
            return out
        """,
        why="""A nested loop join compares every left row with every right row: O(n × m). Building a dict index on one side makes
        each lookup O(1), so the whole join is O(n + m + output): this is the **hash join** that databases use when joining on
        equality without a usable index. The index maps each key value to a **list** because keys can repeat on the right, which
        produces one output row per match, exactly like SQL. `{**row, **match}` builds new dicts, so the inputs are untouched
        (2.4), and the right side wins on clashing column names. pandas `merge` does this on whole columns."""),
    predict("Building dicts with repeats", "hard",
        code="""
        print(dict.fromkeys("abca"))
        print({c: i for i, c in enumerate("abca")})
        print(dict(zip("abc", [1, 2])))
        d = {}
        d["x"] = d.get("x", []) + [1]
        d["x"] = d.get("x", []) + [2]
        print(d, {**{"x": 1}, "x": 2, **{"y": 3}})
        e = {}
        print(e.setdefault("k", []) is e.setdefault("k", ["other"]), e)
        """,
        hints=["A repeated key keeps the first position and the last value. `zip` stops at the shorter input.",
               "`setdefault` only stores its default the first time."],
        why="""`fromkeys` keeps each character once in first-seen order. The comprehension also keeps first positions, but the
        value for `"a"` is overwritten by the later index 3. `zip` stops at the shorter iterable, so `"c"` is dropped without
        an error (1.2's `strict=True` would catch it). Building the list with `d.get("x", []) + [...]` creates a new list each
        time and stores it, which works but copies. In the literal, later keys override earlier ones, including those spread
        from another dict. The second `setdefault` finds the existing key, ignores `["other"]` and returns the same list."""),
)

section("interview", "Interview questions",
    explain("How does a Python dict give O(1) lookups and keep insertion order at the same time?", "medium", tag="Interview",
        why="""It is a hash table: the key's hash picks a slot, collisions are resolved by probing, and the table resizes as it
        fills, so lookups, inserts and deletes are O(1) on average. Since CPython 3.6 (and guaranteed by the language from 3.7),
        it uses a **compact** layout: a small index array of slots points into a separate, dense array of entries stored in
        insertion order. Lookups go through the index; iteration walks the dense entries, which gives insertion order and uses
        less memory than storing entries directly in the sparse table. Keys must be hashable and must not change their hash.
        Mention that deleting and re-inserting a key moves it to the end, and that equality ignores order."""),
    explain("A key might be missing. When do you use `d[k]`, `get`, `setdefault`, `defaultdict` or `try/except KeyError`?", "medium", tag="Interview",
        why="""`d[k]` when the key must exist and a missing key is a bug you want to surface. `d.get(k, default)` for optional
        keys when you only read. `setdefault(k, default)` when you want to read **and** create the entry if absent in one step,
        typically to append to a list (`d.setdefault(k, []).append(x)`). `collections.defaultdict(factory)` when a whole dict
        should create entries on first access, such as counters and grouping (4.6). `try/except KeyError` when the key is
        normally present and the missing case is rare and needs special handling (EAFP style, Module 8). Pitfalls worth
        mentioning: `get(k) or default` swallows falsy values, and `defaultdict` creates entries even on plain reads."""),
    explain("Explain the hash join. When is it better than a nested loop join, and what does it cost?", "hard", tag="Interview",
        why="""For an equality join, build a hash table (a dict) from the smaller input, keyed by the join column, mapping each
        key to its rows; then scan the larger input and look each row's key up. That is O(n + m) time plus the output, versus
        O(n × m) for comparing every pair in nested loops. The cost is memory for the hash table, which is why databases build it
        on the smaller side and spill to disk when it does not fit. It only works for equality conditions (not `<` or ranges,
        where sort-merge joins or indexes are used). In Python this is the dict-of-lists index pattern, and pandas `merge` does
        the same on whole columns. Mention duplicates on both sides multiply output rows, exactly as in SQL."""),
)

recap(
    "A dict is a hash table of keys with values: lookups by key are O(1), keys must be hashable, and insertion order is kept.",
    "`d[k]` for required keys, `get` for optional ones, `in` to test, `setdefault` to read-or-create. Never `get(k) or default` for values that can be 0.",
    "Views (`keys`, `values`, `items`) are live. Never add or delete keys while iterating: loop over a snapshot or build a new dict.",
    "Merges are later-wins and shallow: write layers from lowest to highest priority, `defaults | env | user`.",
    "Inverting loses repeated values; sorting builds a new dict; a dict index of lists turns a nested-loop join into a hash join.",
)
