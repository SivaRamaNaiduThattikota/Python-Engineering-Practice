from lesson import *

lesson(
    id="m4-4", num="4.4", title="Sets and hashing",
    intro="How a hash table finds an item without searching, why that makes membership O(1), set algebra as SQL's UNION, "
          "INTERSECT and EXCEPT, why set order can change between runs (a reproducibility trap), `frozenset`, and the "
          "rule that equal values must hash alike.",
    desc="Hashable values, O(1) membership, union, intersection, difference, `frozenset`.",
    keys="set hash hashable hash table bucket collision membership o(1) union intersection difference symmetric subset superset disjoint frozenset order pythonhashseed determinism dedupe eq hash contract",
)

term("Hash", "A number computed from a value by `hash(x)`. Equal values always have equal hashes; it decides where a value is stored in a set or dict.")
term("Hash table", "The structure behind sets and dicts: slots chosen by hash, so an item is found by computing where it should be, not by searching.")
term("Hashable", "A value whose hash cannot change during its life, so it can be stored in a set or used as a dict key. Immutable built-ins are hashable.")
term("Set algebra", "Union `|`, intersection `&`, difference `-` and symmetric difference `^`: combining sets like SQL's UNION, INTERSECT and EXCEPT.")
term("frozenset", "An immutable, hashable set. It can be a dict key or an element of another set.")

HASH_FIG = """
<svg viewBox="0 0 640 150" role="img" aria-label="To look up 'refund', Python computes its hash, maps it to slot 5, and compares only the item in that slot.">
  <defs><marker id="h1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" style="fill:var(--label2)"/></marker></defs>
  <rect x="10" y="50" width="100" height="40" rx="10" class="box a"/><text x="60" y="75" class="w mid">"refund"</text>
  <rect x="150" y="50" width="130" height="40" rx="10" class="box b"/><text x="215" y="68" class="w mid">hash(...)</text><text x="215" y="84" class="w mid">% 8 slots = 5</text>
  <path d="M110 70 L146 70" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#h1)"/>
  <rect x="320" y="20" width="300" height="24" rx="6" class="box"/><text x="335" y="37">0  "invoice"</text>
  <rect x="320" y="46" width="300" height="24" rx="6" class="box"/><text x="335" y="63">1  (empty)</text>
  <rect x="320" y="72" width="300" height="24" rx="6" class="box"/><text x="335" y="89">2  "login"</text>
  <rect x="320" y="98" width="300" height="24" rx="6" class="box a"/><text x="335" y="115" class="w">5  "refund"   one comparison: found</text>
  <path d="M280 70 C 300 70, 300 110, 316 110" style="stroke:var(--label2);stroke-width:2;fill:none" marker-end="url(#h1)"/>
  <text x="470" y="142" class="mid">(slots 3, 4, 6, 7 not shown)</text>
</svg>"""

section("hashing", "How a set finds an item without searching",
    p("""A set is a **hash table**: an array of slots where each value's position is **computed from the value itself**.
    Step by step, adding or looking up `x` works like this:"""),
    p("""- **1. Hash.** Python calls `hash(x)`, which turns the value into a large integer. Equal values always give equal
      hashes.
    - **2. Pick a slot.** The hash is reduced to a slot number in the table (think `hash % number_of_slots`).
    - **3. Compare.** If that slot is empty, `x` is not in the set. If it holds an item, Python checks identity, then
      equality (2.1). If it holds a different item (a **collision**), it probes a few other slots in a fixed pattern.
    - **4. Grow.** When the table gets about two-thirds full, it is rebuilt with more slots, like a list resize (4.1)."""),
    fig(HASH_FIG, "Membership costs one hash and usually one comparison, however many items the set holds."),
    p("""Because the slot is computed rather than searched for, `x in s`, `s.add(x)` and `s.discard(x)` are **O(1) on
    average**, whether the set holds ten items or ten million. The price: a set has **no meaningful order** (items sit
    wherever their hashes put them), it uses more memory than a list, and it can only store **hashable** values."""),
    ex("""
    print(hash("refund") == hash("re" + "fund"), hash(42), hash((1, 2)) == hash((1, 2)))
    tags = {"billing", "eu", "billing", "refund"}      # duplicates collapse
    print(len(tags), "eu" in tags, "us" in tags)
    try:
        {["a"], ["b"]}
    except TypeError as e:
        print("TypeError:", e)
    """, "hashing.py"),
    callout("sql", "SQL / Power BI", """A set is like a column with a **unique index**: duplicates are rejected and a lookup
    by value is a single seek instead of a table scan. `x in my_list` is the full-scan query; `x in my_set` is the indexed
    one. Power BI's `DISTINCT()` and relationship lookups rely on the same idea."""),
)

section("membership", "Membership at scale: when to convert",
    p("""The most common speed-up in data code is replacing a list membership test inside a loop with a set. Checking
    100,000 ids against a list of 100,000 known ids is 100,000 × O(n) = billions of comparisons; against a set it is
    100,000 × O(1). Building the set costs one pass, O(n), so it pays off as soon as you test membership more than a few
    times."""),
    ex("""
    import time

    known = list(range(0, 100_000, 2))
    queries = list(range(0, 1_000))

    start = time.perf_counter()
    hits_list = sum(1 for q in queries if q in known)
    t_list = time.perf_counter() - start

    known_set = set(known)
    start = time.perf_counter()
    hits_set = sum(1 for q in queries if q in known_set)
    t_set = time.perf_counter() - start

    print(hits_list == hits_set, f"set is about {t_list / t_set:.0f}x faster here")
    """, "membership.py"),
    p("""The exact factor depends on the data and the machine, but it grows with the size of the list: the list scan gets
    slower as the list grows, while the set lookup does not. Convert **once**, outside the loop; `if q in set(known)`
    inside the loop rebuilds the set every time and is even slower than the list."""),
)

section("algebra", "Set algebra",
    p("""Sets support the operations of the SQL set operators, each building a **new** set:"""),
    html("""<div class="tbl"><table>
      <tr><th>Operation</th><th>Operator</th><th>Method</th><th>SQL</th><th>Meaning</th></tr>
      <tr><td>union</td><td><code>a | b</code></td><td><code>a.union(b)</code></td><td><code>UNION</code></td><td>in either</td></tr>
      <tr><td>intersection</td><td><code>a &amp; b</code></td><td><code>a.intersection(b)</code></td><td><code>INTERSECT</code></td><td>in both</td></tr>
      <tr><td>difference</td><td><code>a - b</code></td><td><code>a.difference(b)</code></td><td><code>EXCEPT</code></td><td>in a, not in b</td></tr>
      <tr><td>symmetric difference</td><td><code>a ^ b</code></td><td><code>a.symmetric_difference(b)</code></td><td>(full outer join, mismatches)</td><td>in exactly one</td></tr>
      <tr><td>subset / superset</td><td><code>a &lt;= b</code>, <code>a &gt;= b</code></td><td><code>a.issubset(b)</code></td><td></td><td>every item of a is in b</td></tr>
    </table></div>"""),
    ex("""
    required = {"title", "priority", "owner"}
    returned = {"title", "owner", "confidence"}          # keys an LLM put in its JSON
    print(required - returned)                          # missing fields
    print(returned - required)                          # unexpected fields
    print(sorted(required & returned), required <= returned)
    print(sorted(required ^ returned))
    print(sorted(required.union(["due", "title"])))     # methods accept any iterable
    """, "set_algebra.py"),
    p("""Two practical details. The **operators** need sets on both sides, while the **methods** accept any iterable
    (`a.union(some_list)`), which saves a conversion. And there are in-place versions that change the left set instead of
    building a new one: `a |= b`, `a &= b`, `a -= b`, or `a.update(b)`, `a.difference_update(b)`."""),
)

section("order", "Order and determinism",
    p("""A set has no guaranteed order. Iterating over a set of small integers often looks sorted, which misleads people,
    but that is a side effect of small integers hashing to themselves. For **strings**, Python randomises the hash function
    **per process** (a protection against attacks that feed a server many colliding keys), so the iteration order of a set
    of strings can differ from one run of your program to the next. The values are the same; only the order changes."""),
    ex("""
    import os
    print(os.environ.get("PYTHONHASHSEED", "not set (random per run)"))

    words = ["refund", "invoice", "login", "agent", "embedding", "chunk"]
    unique = set(words)
    print(len(unique), sorted(unique))          # sorted: the same every run
    print(list(dict.fromkeys(words)))           # first-seen order, the same every run
    """, "order.py"),
    callout("warn", "A reproducibility trap in ML", """Code like `labels = list(set(df["label"]))` gives the classes an order
    that can change between runs, so "class 0" may be `"spam"` today and `"ham"` tomorrow, and a saved model's outputs get
    mapped to the wrong names. Build anything that needs a stable order with `sorted(set(...))` or `dict.fromkeys(...)`.
    Setting `PYTHONHASHSEED` makes the order repeatable, but does not make it meaningful."""),
)

section("frozen", "`frozenset`, and the rule that equal values hash alike",
    p("""A `set` is mutable, so it is **not** hashable: you cannot put a set inside a set or use it as a dict key. A
    **`frozenset`** is the immutable version, with the same operations except those that change it, and it is hashable.
    It is the right key for anything **unordered**: a pair of documents `{a, b}` where `(a, b)` and `(b, a)` should be the
    same, a combination of tags, the set of tools an agent may use."""),
    ex("""
    similar = {}
    for a, b, score in [("d1", "d2", 0.91), ("d2", "d1", 0.91), ("d3", "d1", 0.40)]:
        similar[frozenset((a, b))] = score       # (d1, d2) and (d2, d1) are one key
    print(len(similar), similar[frozenset(("d1", "d2"))])
    print(frozenset("ab") == frozenset("ba"), {frozenset({1, 2}), frozenset({2, 1})})
    """, "frozenset.py"),
    p("""Hashing relies on one contract: **if `a == b`, then `hash(a) == hash(b)`**. Python's numbers keep it across types,
    so `1`, `1.0` and `True` are equal, hash alike, and count as **the same element**: the set keeps whichever arrived
    first. That surprises people who mix flags and numbers in one collection. NaN is the opposite case: it is not equal to
    itself, so separate NaN objects are separate elements (2.1)."""),
    ex("""
    print({1, 1.0, True}, {True, 1, 1.0}, len({0, False, 0.0, "0"}))
    print({float("nan"), float("nan")}, len({float("nan"), float("nan")}))
    """, "eq_hash.py"),
)

section("warmup", "Warm-up",
    predict("Sets drop duplicates, not order you rely on", "easy",
        code="""
        ids = [3, 1, 3, 2, 1]
        s = set(ids)
        print(len(s), 2 in s, 5 in s)
        print(sorted(s), list(dict.fromkeys(ids)))
        s.add(2)
        s.discard(99)
        print(len(s))
        try:
            s.remove(99)
        except KeyError as e:
            print("KeyError:", e)
        """,
        hints=["`discard` ignores a missing item; `remove` raises."],
        why="""The set keeps three distinct ids. Adding an existing value changes nothing, and `discard` of a missing value is
        silent, while `remove` raises `KeyError`. For a deduplicated list in a stable order, use `sorted(set(...))` or
        `dict.fromkeys(...)` (first-seen order): never rely on the order of the set itself."""),
    write("Missing and unexpected JSON fields", "easy", tag="GenAI",
        prompt="""Write `check_fields(record, required, optional=())` for a dict produced by an LLM. Return a dict with
        `"missing"`: sorted list of required keys not present, and `"unexpected"`: sorted list of keys that are neither
        required nor optional. Use set operations.""",
        code="""
        def check_fields(record, required, optional=()):
            pass
        """,
        tests="""
        r = {"title": "Refund", "owner": "ana", "mood": "angry"}
        assert check_fields(r, ["title", "priority", "owner"]) == {"missing": ["priority"], "unexpected": ["mood"]}
        assert check_fields(r, ["title"], optional=["owner", "mood"]) == {"missing": [], "unexpected": []}
        assert check_fields({}, ["a", "b"]) == {"missing": ["a", "b"], "unexpected": []}
        """,
        hints=["`record.keys()` behaves like a set already: `set(required) - record.keys()` works."],
        solution="""
        def check_fields(record, required, optional=()):
            keys = set(record)
            required = set(required)
            return {
                "missing": sorted(required - keys),
                "unexpected": sorted(keys - required - set(optional)),
            }
        """,
        why="""Difference answers both questions in one expression each: required minus present is missing, present minus
        allowed is unexpected. Sorting the results makes the output deterministic, which matters for logs and for tests (the
        set order could differ between runs). Validating an LLM's JSON this way before using it, and sending the
        missing/unexpected lists back to the model, is a common repair loop; schema validators like Pydantic report the same
        information in more detail (Module 11)."""),
    fix("A loop that checks membership in a list", "easy", tag="Data work",
        prompt="""`new_customers` is correct but painfully slow on real data (hundreds of thousands of ids). Make it fast
        without changing the result or its order.""",
        code="""
        def new_customers(today, known):
            return [c for c in today if c not in known]
        """,
        tests="""
        today = ["c5", "c1", "c9", "c5", "c7"]
        known = ["c1", "c2", "c7"]
        assert new_customers(today, known) == ["c5", "c9", "c5"]
        assert new_customers([], known) == []
        class CountingList(list):
            checks = 0
            def __contains__(self, item):
                CountingList.checks += 1
                return super().__contains__(item)
        watched = CountingList(f"c{i}" for i in range(50_000))
        assert new_customers(["c3", "x1", "c7"], watched) == ["x1"]
        assert CountingList.checks == 0, f"{CountingList.checks} linear scans of the list"
        """,
        hints=["Build a set from `known` once, before the comprehension.",
               "The last test counts how many times `in` is used on the list itself. The fast version never does."],
        solution="""
        def new_customers(today, known):
            known_set = set(known)
            return [c for c in today if c not in known_set]
        """,
        why="""`c not in known` scans the list for every customer, so the whole function is O(len(today) × len(known)). Building the
        set once makes each check O(1), for O(len(today) + len(known)) overall. The comprehension still walks `today` in order,
        so the result keeps its order and its duplicates; only the lookup structure changed. This is the same as SQL `WHERE id
        NOT IN (...)` against an indexed table versus an unindexed one."""),
    predict("Set operators", "easy",
        code="""
        a = {"search", "calc", "weather"}
        b = {"calc", "email", "search"}
        print(sorted(a | b))
        print(sorted(a & b), sorted(a - b), sorted(b - a), sorted(a ^ b))
        print({"calc"} <= a, a <= a, a < a, a.isdisjoint({"email"}))
        """,
        hints=["`<=` is subset, `<` is proper subset (a subset that is not equal)."],
        why="""Union has every tool from both, intersection the shared ones, and the two differences are not symmetric:
        `a - b` is what only `a` has. Symmetric difference is what exactly one side has. A set is a subset of itself but not a
        **proper** subset, and `isdisjoint` is `True` when nothing is shared."""),
)

section("medium", "Medium",
    write("Agreement between two annotators", "medium", tag="ML",
        prompt="""Two annotators tagged the same documents. Each gives a dict from document id to a **set** of tags. Write
        `agreement(a, b)` returning, for every document in both, the Jaccard similarity of the two tag sets: size of the
        intersection divided by size of the union (1.0 when both are empty). Return a dict, and include only shared document
        ids.""",
        code="""
        def agreement(a, b):
            pass
        """,
        tests="""
        ann1 = {"d1": {"refund", "billing"}, "d2": {"login"}, "d3": set(), "d9": {"x"}}
        ann2 = {"d1": {"refund", "eu"}, "d2": {"login"}, "d3": set()}
        out = agreement(ann1, ann2)
        assert out == {"d1": 1 / 3, "d2": 1.0, "d3": 1.0}
        assert agreement({}, ann2) == {}
        """,
        hints=["The shared ids are `a.keys() & b.keys()`. For each, `len(x & y) / len(x | y)`, with a guard for an empty union."],
        solution="""
        def agreement(a, b):
            out = {}
            for doc in a.keys() & b.keys():
                x, y = a[doc], b[doc]
                union = x | y
                out[doc] = len(x & y) / len(union) if union else 1.0
            return out
        """,
        why="""Dict key views support set operations directly, so `a.keys() & b.keys()` finds the shared documents without building
        lists. Jaccard similarity is the standard way to compare two sets: it is used for annotator agreement on multi-label
        data, for near-duplicate detection (MinHash approximates it at scale), and for comparing retrieved document sets between
        two RAG configurations. The guard defines two empty tag sets as full agreement, a choice worth stating explicitly
        because `0 / 0` has no natural answer."""),
    fix("Classes in a different order every run", "medium", tag="ML",
        prompt="""`encode_labels` maps each class name to an integer for training. On some runs `"spam"` is 0, on others it is
        1, so a saved model's predictions get decoded to the wrong names. Make the mapping deterministic: classes numbered in
        **sorted** order.""",
        code="""
        def encode_labels(labels):
            classes = list(set(labels))
            mapping = {c: i for i, c in enumerate(classes)}
            return [mapping[l] for l in labels], classes
        """,
        tests="""
        codes, classes = encode_labels(["spam", "ham", "spam", "eggs"])
        assert classes == ["eggs", "ham", "spam"]
        assert codes == [2, 1, 2, 0]
        assert encode_labels([]) == ([], [])
        """,
        hints=["`list(set(...))` has no guaranteed order. Which function gives a stable order of the distinct labels?"],
        solution="""
        def encode_labels(labels):
            classes = sorted(set(labels))
            mapping = {c: i for i, c in enumerate(classes)}
            return [mapping[l] for l in labels], classes
        """,
        why="""The iteration order of a set of strings depends on the per-process hash seed, so `list(set(labels))` can order the
        classes differently on different runs, and the integer codes change with it. `sorted(set(labels))` is deterministic.
        scikit-learn's `LabelEncoder` does exactly this, keeping the sorted classes in `classes_`; saving that list together
        with the model is how predictions are decoded back to names later."""),
    trace("Building a set step by step", "medium",
        prompt="Fill in the set (shown sorted) and its size after each marked line.",
        code="""
        s = set()
        s.add("Refund")  # row: "s.add('Refund')"
        s |= {"refund", "Refund"}  # row: "s |= {'refund', 'Refund'}"
        s = {x.lower() for x in s}  # row: "lower-case every item"
        s -= {"invoice"}  # row: "s -= {'invoice'}"
        s.update(["login", "refund"])  # row: "s.update([...])"
        """,
        trace_vars=["sorted(s)", "len(s)"],
        hints=["Strings that differ in case are different values. `-=` with an item that is not there changes nothing."],
        why="""`"Refund"` and `"refund"` are different strings, so after the union the set has two items. Lower-casing builds a
        **new** set in which both become `"refund"`, so it collapses to one item: normalising before deduplicating is what
        actually merges variants. Removing an absent item with `-=` is silently fine, and `update` adds only `"login"`, since
        `"refund"` is already present."""),
    choose("Deduplicate a long list, keeping order", "medium",
        prompt="Both remove repeats from 10,000 ids while keeping first-seen order. Which is faster?",
        setup="""import random
random.seed(2)
ids = [random.randrange(3_000) for _ in range(10_000)]""",
        options={
            "a": "out = []\nfor x in ids:\n    if x not in out:\n        out.append(x)",
            "b": "out = list(dict.fromkeys(ids))",
        },
        answer="b",
        hints=["How long is `out` when the loop is near the end, and what does `x not in out` cost then?"],
        why="""A checks membership in a growing **list**, so each check costs up to 3,000 comparisons: O(n × distinct). B inserts
        each id into a dict (a hash table), O(1) each, and dicts keep insertion order, so `list(dict.fromkeys(ids))` is the
        idiomatic ordered dedupe. An explicit `seen = set()` loop has the same complexity and is the version to write when you
        also need to do something with each new item."""),
    write("Changed, added and removed documents", "medium", tag="RAG",
        prompt="""A RAG index must be refreshed. Given `old` and `new`, dicts from document id to a content hash, write
        `diff_index(old, new)` returning a dict with sorted lists `"added"`, `"removed"` and `"changed"` (in both, different
        hash). Only these documents need re-embedding or deleting.""",
        code="""
        def diff_index(old, new):
            pass
        """,
        tests="""
        old = {"a": "h1", "b": "h2", "c": "h3"}
        new = {"b": "h2", "c": "h9", "d": "h4"}
        assert diff_index(old, new) == {"added": ["d"], "removed": ["a"], "changed": ["c"]}
        assert diff_index({}, {}) == {"added": [], "removed": [], "changed": []}
        """,
        hints=["Use the key views: `new.keys() - old.keys()`, `old.keys() - new.keys()`, and `old.keys() & new.keys()` for the candidates for \"changed\"."],
        solution="""
        def diff_index(old, new):
            both = old.keys() & new.keys()
            return {
                "added": sorted(new.keys() - old.keys()),
                "removed": sorted(old.keys() - new.keys()),
                "changed": sorted(k for k in both if old[k] != new[k]),
            }
        """,
        why="""Set differences on the key views find added and removed documents in O(n), and only the shared ids need a value
        comparison. Comparing content **hashes** (for example a SHA-256 of the text) instead of the text itself keeps the
        stored state small. Re-embedding only what changed is the difference between an index refresh that costs a few cents and
        one that re-embeds the whole corpus; incremental indexing in LlamaIndex and LangChain's indexing API work this way."""),
    fix("Pairs counted twice", "medium", tag="Data work",
        prompt="""`count_pairs` counts how often two products are bought together. `("milk", "bread")` and `("bread",
        "milk")` are counted as different pairs. Fix it so the order inside a pair does not matter.""",
        code="""
        def count_pairs(baskets):
            counts = {}
            for basket in baskets:
                items = list(basket)
                for i in range(len(items)):
                    for j in range(i + 1, len(items)):
                        pair = (items[i], items[j])
                        counts[pair] = counts.get(pair, 0) + 1
            return counts
        """,
        tests="""
        baskets = [["milk", "bread"], ["bread", "milk", "eggs"], ["eggs", "milk"]]
        c = count_pairs(baskets)
        assert c[frozenset({"milk", "bread"})] == 2
        assert c[frozenset({"milk", "eggs"})] == 2
        assert c[frozenset({"bread", "eggs"})] == 1
        assert len(c) == 3
        """,
        hints=["Use a key that is the same whatever the order: a `frozenset` of the two items."],
        solution="""
        def count_pairs(baskets):
            counts = {}
            for basket in baskets:
                items = list(basket)
                for i in range(len(items)):
                    for j in range(i + 1, len(items)):
                        pair = frozenset((items[i], items[j]))
                        counts[pair] = counts.get(pair, 0) + 1
            return counts
        """,
        why="""A tuple remembers order, so the same pair in two orders makes two keys. A `frozenset` has no order and is hashable,
        so both orders give one key. `tuple(sorted(...))` would also work and is easier to read in printed output. This
        co-occurrence counting is the first step of market-basket analysis (association rules) and of building co-occurrence
        features for recommendation; `itertools.combinations(items, 2)` replaces the two index loops."""),
    refactor("Membership with a set literal", "medium",
        prompt="Simplify this allow-list check. It must still accept exactly the same names. Keep the tests green.",
        code="""
        def is_allowed(tool):
            if tool == "search" or tool == "calculator" or tool == "weather" or tool == "translate":
                return True
            else:
                return False
        """,
        tests="""
        assert all(is_allowed(t) for t in ["search", "calculator", "weather", "translate"])
        assert not is_allowed("delete_files") and not is_allowed("Search")
        """,
        hints=["Put the names in a module-level set and test `in`."],
        solution="""
        ALLOWED_TOOLS = frozenset({"search", "calculator", "weather", "translate"})

        def is_allowed(tool):
            return tool in ALLOWED_TOOLS
        """,
        why="""The chain of `==` comparisons is a hand-written linear search; a set states the rule as data, gives O(1) lookups,
        and can be shown, logged or loaded from configuration. Making it a `frozenset` at module level means nothing can add a
        tool to the allow-list by accident at run time, which matters for an agent's security boundary. Comparison is still
        exact and case-sensitive, so `"Search"` stays rejected."""),
)

section("hard", "Hard",
    predict("When 1, 1.0 and True collide", "hard",
        code="""
        flags = {True, 1, 1.0, 0, False}
        print(flags, len(flags))
        print({1.0, 1, True}, {"a": 1, True: "x", 1: "y"})
        mixed = [1, "1", 1.0, True, 2]
        print(len(set(mixed)), sorted(set(mixed), key=repr))
        print(hash(1) == hash(1.0) == hash(True), 0.1 + 0.2 in {0.3})
        """,
        hints=["Equal values must hash alike, and `True == 1 == 1.0`. A set keeps the first of equal elements it saw."],
        why="""`True`, `1` and `1.0` are equal and hash alike, so they are **one** element; the set keeps the first that arrived
        (`True` in the first set, `1.0` in the second), and the same applies to `0` and `False`. In the dict, `True` and `1` are
        the same key, so the later value `"y"` overwrites `"x"` while the key stays `True`. `"1"` is a string, different from the
        number. Finally, `0.1 + 0.2` is not exactly `0.3` (1.1), so it is not found: sets compare exactly, so never use them to
        deduplicate floats that were computed, round first."""),
    write("Near-duplicate chunks with shingles", "hard", tag="RAG",
        prompt="""Write `shingles(text, k=3)` returning the set of all `k`-word sequences (as tuples) of the lower-cased
        words, and `near_duplicates(chunks, threshold)` returning the sorted list of index pairs `(i, j)`, `i < j`, whose
        shingle sets have Jaccard similarity at least `threshold`. Texts shorter than `k` words have one shingle: the tuple of
        all their words.""",
        code="""
        def shingles(text, k=3):
            pass

        def near_duplicates(chunks, threshold):
            pass
        """,
        tests="""
        assert shingles("a b c d") == {("a", "b", "c"), ("b", "c", "d")}
        assert shingles("Hi there", k=3) == {("hi", "there")}
        chunks = [
            "Refunds are processed within five business days of the request",
            "refunds are processed within five business days of your request",
            "Contact support to change your shipping address",
            "Refunds are processed within five business days",
        ]
        assert near_duplicates(chunks, 0.5) == [(0, 1), (0, 3), (1, 3)]
        assert near_duplicates(chunks, 0.99) == []
        assert near_duplicates([], 0.5) == []
        """,
        hints=["Shingles: `{tuple(words[i:i + k]) for i in range(len(words) - k + 1)}`, with a special case for short texts.",
               "Compute every chunk's shingle set once, then compare each pair `i < j` with `len(a & b) / len(a | b)`."],
        solution="""
        def shingles(text, k=3):
            words = text.lower().split()
            if len(words) < k:
                return {tuple(words)}
            return {tuple(words[i:i + k]) for i in range(len(words) - k + 1)}

        def near_duplicates(chunks, threshold):
            sets = [shingles(c) for c in chunks]
            out = []
            for i in range(len(sets)):
                for j in range(i + 1, len(sets)):
                    union = sets[i] | sets[j]
                    if union and len(sets[i] & sets[j]) / len(union) >= threshold:
                        out.append((i, j))
            return out
        """,
        why="""Word shingles turn "how similar is this text" into "how much do these sets overlap", and tuples are used because a
        list cannot go in a set. Chunks 0 and 1 differ in one word, so most shingles survive; chunk 3 is a truncated copy, so its
        shingles are a subset of chunk 0's, and shares the same five shingles with chunk 1. Comparing every pair is O(n²), fine for hundreds of chunks; at corpus scale, MinHash with
        locality-sensitive hashing estimates Jaccard similarity and only compares likely candidates. Removing near-duplicate
        chunks before indexing stops a RAG system from filling its context with the same passage several times."""),
    fix("Read the code: an allow-list with three holes", "hard", tag="GenAI",
        prompt="""This guards which tools an agent may call. A security review found three problems: a tool can be enabled
        for everyone at run time by mistake, a tool name with different case or spaces slips past the deny-list, and the
        user's effective permissions are printed in a different order on each run, which breaks the audit log diff. Fix all
        three without changing which tools are allowed.""",
        code="""
        BASE_TOOLS = {"search", "calculator"}
        DENIED = ["delete_files", "send_email"]


        def tools_for(user_extra):
            allowed = BASE_TOOLS
            allowed |= set(user_extra)
            return allowed - set(DENIED)


        def can_call(user_extra, tool):
            return tool in tools_for(user_extra)


        def audit_line(user, user_extra):
            return f"{user}: {', '.join(tools_for(user_extra))}"
        """,
        tests="""
        assert tools_for(["weather"]) == {"search", "calculator", "weather"}
        assert tools_for([]) == {"search", "calculator"}
        assert not can_call(["Delete_Files "], "delete_files")
        assert not can_call(["Send_Email"], "send_email")
        assert can_call(["Weather"], "weather")
        assert audit_line("ana", ["weather"]) == "ana: calculator, search, weather"
        assert BASE_TOOLS == {"search", "calculator"}
        """,
        hints=["`allowed = BASE_TOOLS` is an alias, and `|=` changes that shared set in place (2.2).",
               "Normalise names (`strip().lower()`) before comparing them with the deny-list and the allow-list.",
               "The audit line joins a set: sort it first."],
        solution="""
        BASE_TOOLS = frozenset({"search", "calculator"})
        DENIED = frozenset({"delete_files", "send_email"})


        def normalise(name):
            return name.strip().lower()


        def tools_for(user_extra):
            return (BASE_TOOLS | {normalise(t) for t in user_extra}) - DENIED


        def can_call(user_extra, tool):
            return normalise(tool) in tools_for(user_extra)


        def audit_line(user, user_extra):
            return f"{user}: {', '.join(sorted(tools_for(user_extra)))}"
        """,
        why="""Hole one is aliasing (2.2): `allowed = BASE_TOOLS` then `allowed |= ...` adds the user's extra tools to the
        **global** base set, so one user's grant leaks to every later user. The `|` operator builds a new set, and making the
        base a `frozenset` turns any future in-place change into an error. Hole two is normalisation: sets compare exactly, so
        `"Delete_Files "` is not `"delete_files"`; normalising both the grants and the requested tool closes the bypass. Hole
        three is order: joining a set gives a hash-dependent order, so the audit text changes between runs; `sorted` makes it
        deterministic. All three are real classes of bugs in agent permission code."""),
    write("Hashable records for deduplication", "hard", tag="Data work",
        prompt="""Rows from two CRM exports are dicts that may contain list values (tags). Write `dedupe_rows(rows, keys)`
        that keeps the first row for each distinct combination of the values in `keys`, in input order. Two rows are the same
        if their values for `keys` are equal, treating a list of tags as **unordered** (so `["a", "b"]` equals `["b",
        "a"]`). Missing keys count as `None`.""",
        code="""
        def dedupe_rows(rows, keys):
            pass
        """,
        tests="""
        rows = [{"email": "ana@x.io", "tags": ["vip", "eu"], "src": "crm1"},
                {"email": "ana@x.io", "tags": ["eu", "vip"], "src": "crm2"},
                {"email": "ana@x.io", "tags": ["eu"], "src": "crm2"},
                {"email": "ben@x.io", "src": "crm1"},
                {"email": "ben@x.io", "tags": None, "src": "crm2"}]
        out = dedupe_rows(rows, ["email", "tags"])
        assert [r["src"] for r in out] == ["crm1", "crm2", "crm1"]
        assert len(dedupe_rows(rows, ["email"])) == 2
        assert dedupe_rows([], ["email"]) == []
        """,
        hints=["Build a hashable key per row: a tuple of the values for `keys`, turning lists into `frozenset`s.",
               "`row.get(k)` gives `None` for a missing key, so a missing `tags` and `tags: None` produce the same key."],
        solution="""
        def to_hashable(value):
            return frozenset(value) if isinstance(value, list) else value

        def dedupe_rows(rows, keys):
            seen = set()
            out = []
            for row in rows:
                key = tuple(to_hashable(row.get(k)) for k in keys)
                if key not in seen:
                    seen.add(key)
                    out.append(row)
            return out
        """,
        why="""Rows are dicts, which cannot go in a set, so deduplication needs a hashable **key** that captures exactly what
        "the same" means: a tuple over the chosen columns, with lists converted to `frozenset` to ignore their order. Choosing
        `frozenset` also ignores duplicates inside the list; if `["eu", "eu"]` must differ from `["eu"]`, use
        `tuple(sorted(value))` instead. Defining equality explicitly like this is the core of record linkage. In pandas,
        `drop_duplicates` fails on list columns for the same unhashable reason, and the fix is the same conversion."""),
)

section("interview", "Interview questions",
    explain("Why is `x in some_set` O(1) but `x in some_list` O(n)?", "medium", tag="Interview",
        why="""A list stores items in order with no index of values, so finding `x` means comparing it with items one by one.
        A set is a hash table: Python computes `hash(x)`, maps it to a slot and compares only the item(s) there, so the cost does
        not depend on how many items the set holds. It is O(1) on **average**; with many collisions (bad hash functions, or
        adversarial keys) it degrades, which is why Python randomises string hashes. The trade-offs: sets use more memory, keep
        no order, and need hashable items. Mention the practical rule: build the set once outside a loop."""),
    explain("What does it mean for an object to be hashable, and what is the contract between `__eq__` and `__hash__`?", "medium", tag="Interview",
        why="""Hashable means the object has a hash value that never changes during its lifetime, so it can be found again in a
        set or dict. The contract: objects that compare equal must have equal hashes (the reverse need not hold; different
        objects may collide). That is why mutable containers like lists, dicts and sets are unhashable: their equality depends
        on contents that can change. It also explains `{1, 1.0, True}` having one element, since those are equal and hash alike.
        For your own classes (Module 9), defining `__eq__` without `__hash__` makes instances unhashable, and you should only
        define `__hash__` from fields that never change; frozen dataclasses do this for you."""),
    explain("A model's predicted class names come out wrong after you reload it. What might sets have to do with it?", "hard", tag="Interview",
        why="""If the class list was built with `list(set(labels))`, its order depends on the per-process string hash seed
        (`PYTHONHASHSEED`), so the integer each class received during training can differ from the one assumed at prediction
        time, and predictions get decoded to the wrong names. No error is raised; accuracy just looks terrible or labels are
        swapped. Fixes: build the class list with `sorted(set(...))` or first-seen order, save it with the model (as
        scikit-learn does in `classes_`), and add a test that decodes known examples after reload. The general lesson: never let
        anything that must be reproducible depend on set or hash iteration order."""),
)

recap(
    "A set is a hash table: `in`, `add` and `discard` are O(1) on average because the slot is computed from the value.",
    "Only hashable values can go in a set. Equal values must hash alike, so `1`, `1.0` and `True` are one element.",
    "Replace list membership in loops with a set built once. `dict.fromkeys` deduplicates while keeping order.",
    "`|`, `&`, `-`, `^` are UNION, INTERSECT, EXCEPT and \"in exactly one\". Dict key views support them too.",
    "Set order is not meaningful and string order can change between runs: sort before you print, number or save anything.",
)
