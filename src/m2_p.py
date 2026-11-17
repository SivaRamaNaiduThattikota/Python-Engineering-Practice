from lesson import *

lesson(
    id="m2-p", num="2.P", title="Module 2 practice set and mini project",
    intro="Mixed problems from all of Module 2: identity, mutability, copies and argument passing, in the order they "
          "turn up in real code. Then a mini project that needs all of it: a safe conversation store for a chat service.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project identity alias copy deepcopy default argument pure function conversation store fork session",
)

section("how", "How to use this page",
    p("""The problems are deliberately not grouped by lesson: part of the skill is recognising which idea a bug comes
    from. Before opening a hint, say out loud which of these it is: identity versus equality (2.1), a shared mutable
    object (2.2), a copy that is too shallow or too deep (2.3), or something a function did to its arguments or
    defaults (2.4)."""),
)

section("set", "Practice set",
    predict("Alias, shallow and deep in one go", "easy",
        code="""
        import copy

        a = {"k": [1]}
        b = a
        c = dict(a)
        d = copy.deepcopy(a)
        a["k"].append(2)
        a["new"] = 0
        print(b)
        print(c)
        print(d)
        """,
        hints=["Two kinds of change happen: one to the inner list, one to the outer dict."],
        why="""`b` is an alias, so it sees both changes. `c` is a shallow copy: it shares the inner list, so it sees the
        append, but adding `"new"` changed only `a`'s outer dict. `d` is a deep copy and shares nothing. Every Module 2
        bug is one of these three relationships."""),
    fix("Default tags that pile up", "easy", tag="Data work",
        prompt="""`tag_doc(doc, tags=["general"])` should return a **new** document with the given tags plus a
        `"seen"` tag. Calls without `tags` keep collecting `"seen"` tags, and the caller's document changes too. Fix both.""",
        code="""
        def tag_doc(doc, tags=["general"]):
            tags.append("seen")
            doc["tags"] = tags
            return doc
        """,
        tests="""
        d = {"id": 1}
        out = tag_doc(d)
        assert out == {"id": 1, "tags": ["general", "seen"]} and d == {"id": 1}
        assert tag_doc({"id": 2}) == {"id": 2, "tags": ["general", "seen"]}
        mine = ["faq"]
        assert tag_doc({"id": 3}, mine)["tags"] == ["faq", "seen"] and mine == ["faq"]
        """,
        hints=["Never change the default or the caller's list: build a new list with `+`.",
               "Return `{**doc, \"tags\": ...}` instead of writing into `doc`."],
        solution="""
        def tag_doc(doc, tags=("general",)):
            return {**doc, "tags": list(tags) + ["seen"]}
        """,
        why="""Three separate side effects: appending to the default, appending to a caller's list, and writing into the
        caller's dict. Building the result with `list(tags) + ["seen"]` and `{**doc, ...}` removes all three. The default
        became a tuple: an immutable default can never be changed by accident, so it is safe to leave in the signature,
        which reads better than `None` when there is a real default value."""),
    predict("Equal tuples and NaN", "medium", tag="ML",
        code="""
        t1 = (1, [2])
        t2 = (1, [2])
        print(t1 == t2, t1 is t2)
        x = float("nan")
        print((x, 1) == (x, 1))
        print((float("nan"), 1) == (float("nan"), 1))
        print(x in {x}, float("nan") in {x})
        """,
        hints=["Tuples compare item by item with \"identity, then equality\". Sets look items up by hash, then identity, then equality."],
        why="""`t1` and `t2` are equal but separate. `(x, 1) == (x, 1)` is `True` because both tuples hold the **same** NaN
        object and the identity check comes first, while two separate NaNs are never equal. Sets follow the same rule: the
        same NaN object is found, a new one is not. A dataset deduplicated with a set can keep "duplicate" rows that both
        contain NaN, which is exactly what you see when deduplicating feature tuples with missing values."""),
    write("Group ids by category", "medium", tag="Data work",
        prompt="""Write `group_ids(records)` that takes `(id, category)` pairs and returns a dict from category to the list
        of ids in that category, in input order. Each category must have **its own** list.""",
        code="""
        def group_ids(records):
            pass
        """,
        tests="""
        out = group_ids([(1, "a"), (2, "b"), (3, "a")])
        assert out == {"a": [1, 3], "b": [2]}
        out["a"].append(99)
        assert out["b"] == [2]
        assert group_ids([]) == {}
        """,
        hints=["Start with `{}` and create a list the first time you meet a category. `dict.setdefault` does it in one call."],
        solution="""
        def group_ids(records):
            out = {}
            for rid, cat in records:
                out.setdefault(cat, []).append(rid)
            return out
        """,
        why="""`setdefault(cat, [])` returns the existing list or stores a new one, and the `[]` is evaluated on each call,
        so each category gets its own list. The tempting `dict.fromkeys(categories, [])` would share one list between all
        categories (2.2). `collections.defaultdict(list)` is the other standard way (lesson 4.6)."""),
    trace("A None default across calls", "medium",
        prompt="Fill in `s`, `t`, `u` and whether `s is u` after each marked line.",
        code="""
        def remember(x, seen=None):
            if seen is None:
                seen = []
            seen.append(x)
            return seen

        s = remember(1)
        t = remember(2)
        u = remember(3, s)  # row: "after the three calls"
        t.append(0)  # row: "t.append(0)"
        s.append(4)  # row: "s.append(4)"
        """,
        trace_vars=["s", "t", "u", "s is u"],
        hints=["Each call without `seen` makes a new list. Passing `s` hands the function that exact list."],
        why="""With the `None` default, the first two calls each build their own list, so `t` is independent of `s`. The
        third call receives `s` itself, appends to it and returns it, so `u` **is** `s` and both show `[1, 3]`.
        `t.append(0)` changes only `t`, while `s.append(4)` also shows through `u`, because they are one list. This is
        the correct version of the mutable-default pattern: fresh by default,
        shared only when the caller asks for it."""),
    choose("1,000 config variants", "medium", tag="ML",
        prompt="""Both create a variant of a config that holds a large stopword list, with one nested value changed.
        Which is faster?""",
        setup="""import copy
config = {"retriever": {"k": 5, "stopwords": [f"w{i}" for i in range(20000)]},
          "llm": {"model": "small", "params": {"temperature": 0.2}}}""",
        options={
            "a": "v = copy.deepcopy(config)\nv[\"llm\"][\"params\"][\"temperature\"] = 0.9",
            "b": "v = {**config, \"llm\": {**config[\"llm\"], \"params\": {**config[\"llm\"][\"params\"], \"temperature\": 0.9}}}",
        },
        answer="b",
        hints=["How many objects does each option create? Does the stopword list need copying at all?"],
        why="""A copies the whole config, including all 20,000 stopword strings' list, just to change one number. B copies
        only the three dicts on the path to `temperature` and shares the retriever branch, which is the structural sharing
        from 2.3, problem 14. The difference grows with the size of the untouched parts, which in real configs (prompt
        libraries, vocabularies, label maps) is most of the config."""),
    fix("Train and test splits that share rows", "hard", tag="ML",
        prompt="""`make_splits` splits rows into train and test. Later, the training rows are normalised **in place**, and
        the original dataset changes with them, so re-running the experiment gives different numbers. Fix `make_splits`
        so each split owns its rows. Do not change `normalise_inplace`.""",
        code="""
        def make_splits(rows, n_train):
            return rows[:n_train], rows[n_train:]


        def normalise_inplace(rows):
            for row in rows:
                total = sum(row)
                row[:] = [v / total for v in row]
        """,
        tests="""
        data = [[1, 1], [1, 3], [2, 2]]
        train, test = make_splits(data, 2)
        normalise_inplace(train)
        assert train == [[0.5, 0.5], [0.25, 0.75]]
        assert data == [[1, 1], [1, 3], [2, 2]]
        assert test == [[2, 2]] and test[0] is not data[2]
        """,
        hints=["A slice is a shallow copy: the split lists are new, but the row lists inside are the dataset's rows.",
               "Copy each row as you build the splits."],
        solution="""
        def make_splits(rows, n_train):
            return [r[:] for r in rows[:n_train]], [r[:] for r in rows[n_train:]]


        def normalise_inplace(rows):
            for row in rows:
                total = sum(row)
                row[:] = [v / total for v in row]
        """,
        why="""Slicing creates new outer lists, which looks like a copy, but the rows inside are the dataset's own row
        objects. Normalising them in place reaches straight into `data`. Copying each row makes the splits own their data,
        so in-place work on them is safe. In numpy the same trap is worse, because `X[:n]` is a **view** of the whole
        array (2.2): normalising `X_train = X[:n]` in place changes `X`. That is why scikit-learn's `train_test_split`
        returns copies."""),
    write("Drop repeated messages, keep the originals", "medium", tag="GenAI",
        prompt="""A client sometimes sends the same message twice in a row. Write `drop_repeats(history)` that returns a new
        list without messages that are **equal** to the message right before them. The messages you keep must be the
        **original objects**, not copies, because other code tracks them by identity.""",
        code="""
        def drop_repeats(history):
            pass
        """,
        tests="""
        m1 = {"role": "user", "content": "hi"}
        m2 = {"role": "user", "content": "hi"}
        m3 = {"role": "assistant", "content": "Hello!"}
        m4 = {"role": "user", "content": "hi"}
        out = drop_repeats([m1, m2, m3, m4])
        assert out == [m1, m3, m4]
        assert out[0] is m1 and out[1] is m3 and out[2] is m4
        assert drop_repeats([]) == []
        """,
        hints=["Compare each message with the **last kept** message using `==`, and append the message object itself."],
        solution="""
        def drop_repeats(history):
            out = []
            for msg in history:
                if not out or msg != out[-1]:
                    out.append(msg)
            return out
        """,
        why="""Two different questions in one function. **Whether** to keep a message is a value question, so it uses `==`
        (two equal "hi" messages in a row are a repeat). **What** to keep is the identity question, so the original object
        goes in the result instead of a copy. `m4` equals `m1` but is kept, because only consecutive repeats count. Good
        code in this module keeps those two questions apart."""),
    predict("Slice assignment versus rebinding a parameter", "medium",
        code="""
        def f(a, b):
            a[:] = [9]
            b = [9]
            return a, b

        x, y = [1, 2], [1, 2]
        ra, rb = f(x, y)
        print(x, y)
        print(ra is x, rb is y)
        """,
        hints=["`a[:] = ...` changes the object `a` points at. `b = ...` moves the local name `b`."],
        why="""`a[:] = [9]` replaces the **contents** of the caller's list, so `x` becomes `[9]` and the returned `a` is `x`
        itself. `b = [9]` only moves the local name, so `y` is untouched and the returned list is a new one. The same two
        lines look almost identical and do opposite things to the caller."""),
    fix("Rename a key without copying everything", "medium",
        prompt="""This renames one key in a record. It deep-copies the whole record to stay safe, which is slow for records
        with big nested values, and it fails the test that the values must be shared, not copied. Rewrite it so the input
        is still never changed and the values are **not** copied.""",
        code="""
        import copy

        def rename_key(record, old, new):
            out = copy.deepcopy(record)
            if old in out:
                out[new] = out[old]
                del out[old]
            return out
        """,
        tests="""
        rec = {"id": 7, "meta": {"src": "crm", "rows": list(range(5))}}
        out = rename_key(rec, "meta", "metadata")
        assert out == {"id": 7, "metadata": {"src": "crm", "rows": [0, 1, 2, 3, 4]}}
        assert "meta" in rec and "metadata" not in rec
        assert out["metadata"] is rec["meta"]
        assert rename_key(rec, "nope", "x") == rec
        """,
        hints=["Build the new dict directly: keep every value, change only the one key name.",
               "A dict comprehension with a conditional key: `{(new if k == old else k): v for ...}`."],
        solution="""
        def rename_key(record, old, new):
            return {(new if k == old else k): v for k, v in record.items()}
        """,
        why="""The function never changes any value, so there is nothing to protect inside them: building a new dict that
        points at the same values is enough to leave the input untouched. Sharing the values is safe as long as callers
        do not change them in place, the same contract as structural sharing. "Deep-copy everything defensively" is a
        common over-correction after an aliasing bug. It costs time and memory and hides the real design question:
        who is allowed to change this data?"""),
    write("Which settings changed?", "hard", tag="GenAI",
        prompt="""Write `changed_paths(old, new)` that compares two nested configs (dicts of dicts and plain values) and
        returns a sorted list of key paths (tuples) whose values differ, including keys that were added or removed. When a
        nested dict is the **same object** in both configs, skip it without looking inside: with structural sharing (2.3),
        that is most of the config.""",
        code="""
        def changed_paths(old, new):
            pass
        """,
        tests="""
        retr = {"k": 5, "index": {"name": "docs", "shards": 4}}
        old = {"retriever": retr, "llm": {"model": "small", "params": {"temperature": 0.2, "top_p": 1.0}}}
        new = {"retriever": retr, "llm": {"model": "small", "params": {"temperature": 0.9}}, "debug": True}
        assert changed_paths(old, new) == [("debug",), ("llm", "params", "temperature"), ("llm", "params", "top_p")]
        assert changed_paths(old, old) == []
        assert changed_paths({"a": {"x": 1}}, {"a": 2}) == [("a",)]
        """,
        hints=["Recurse into a key only when both sides hold a dict; check `is` first and return early when they are the same object.",
               "A key present on one side only is a change. Use the union of both key sets."],
        solution="""
        MISSING = object()

        def changed_paths(old, new, prefix=()):
            if old is new:
                return []
            out = []
            for key in set(old) | set(new):
                a, b = old.get(key, MISSING), new.get(key, MISSING)
                path = prefix + (key,)
                if isinstance(a, dict) and isinstance(b, dict):
                    out.extend(changed_paths(a, b, path))
                elif a != b:
                    out.append(path)
            return sorted(out)
        """,
        why="""The `is` check at the top is the point: comparing shared branches by identity is O(1), so diffing two
        variants built with structural sharing costs time only for the parts that were actually rebuilt. `==` would walk
        every shared branch to find out it is equal to itself. A sentinel (2.1) marks missing keys, because `None` could be
        a real setting value. The `prefix` parameter has an immutable tuple as its default, which is safe. Config diffs
        like this are what experiment trackers show when you compare two runs."""),
    explain("A notebook gives different results when you run its cells a second time. What would you look for?", "hard", tag="Interview",
        why="""Something is being changed in place and reused. In order: a function with a mutable default (a list or dict
        that keeps collecting across calls); a transform that changes its input in place, so running it twice transforms
        twice (scaling, appending features, filling missing values); an alias between "raw" and "processed" data, such as a
        slice or a numpy view, so processing changed the raw data; shared nested config copied shallowly between
        experiments; and global state (a cache or counter at module level). How to confirm: snapshot the input with
        `copy.deepcopy` before a step and compare after, check `id()` or `is` between raw and processed objects, and
        restart the kernel and run top to bottom. The fix is the module's theme: pure functions by default, explicit in-place
        operations, copies at the right depth, `None` defaults."""),
    explain("How do you make sure a function does not change its inputs, and how would you test it?", "medium", tag="Interview",
        why="""Design first: write it as a pure function that builds new objects (`{**d, ...}`, `xs + [...]`,
        comprehensions) instead of changing old ones, and pass read-only data where you can (tuples, `MappingProxyType`,
        frozen dataclasses). To test it: make a deep copy of the input before the call and assert the input still equals that
        snapshot afterwards; also assert that the result is not the same object as the input (`out is not inp`) where a new
        object is promised. For data code, test with nested inputs, because shallow copies only fail there. Property-based
        testing (Hypothesis) can check "input unchanged" across many generated inputs automatically."""),
)

section("project", "Mini project: a safe conversation store",
    p("""A chat service keeps sessions in memory. Earlier versions had every bug from this module: users saw each other's
    messages, deleting one "ok" deleted another, editing a returned history changed the stored one, and forking a
    session for an A/B test changed the original. Build the store so none of that can happen. The tests check every
    rule."""),
    write("A safe conversation store", "hard", key="conversation-store", tag="Project",
        prompt="""Implement these functions over a plain dict `store` (session id to session):

        **1. `start_session(store, session_id, system, settings=None)`**: create a session with a system message
        `{"role": "system", "content": system}` and settings made from `DEFAULTS` with `settings` merged on top (one
        level of nesting, like `DEFAULTS["llm"]`). Starting an existing id raises `ValueError`. No session may share any
        list or dict with `DEFAULTS` or with another session.

        **2. `add_message(store, session_id, role, content)`**: append a new message and **return that message object**.

        **3. `get_history(store, session_id)`**: return the messages so the caller can freely append to the list **or**
        edit any message without changing the store.

        **4. `delete_message(store, session_id, msg)`**: delete **exactly** that message object. Deleting the system
        message, or a message that is not in the session, raises `ValueError`.

        **5. `fork_session(store, source_id, new_id)`**: create `new_id` as an independent copy of `source_id`, messages
        and settings included. Later changes to either session must not show in the other.""",
        code="""
        DEFAULTS = {"llm": {"model": "small", "temperature": 0.2}, "tags": ["chat"]}


        def start_session(store, session_id, system, settings=None):
            pass


        def add_message(store, session_id, role, content):
            pass


        def get_history(store, session_id):
            pass


        def delete_message(store, session_id, msg):
            pass


        def fork_session(store, source_id, new_id):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        store = {}
        start_session(store, "u1", "Be brief.")
        start_session(store, "u2", "Be formal.", {"llm": {"temperature": 0.9}})
        assert store["u2"]["settings"]["llm"] == {"model": "small", "temperature": 0.9}
        assert store["u1"]["settings"]["llm"] == {"model": "small", "temperature": 0.2}
        store["u1"]["settings"]["tags"].append("vip")
        assert DEFAULTS["tags"] == ["chat"] and store["u2"]["settings"]["tags"] == ["chat"]
        assert raises(ValueError, start_session, store, "u1", "again")
        first = add_message(store, "u1", "user", "ok")
        add_message(store, "u1", "assistant", "Noted.")
        second = add_message(store, "u1", "user", "ok")
        assert len(store["u2"]["messages"]) == 1
        h = get_history(store, "u1")
        h.append({"role": "user", "content": "draft"})
        h[1]["content"] = "edited"
        assert [m["content"] for m in store["u1"]["messages"]] == ["Be brief.", "ok", "Noted.", "ok"]
        delete_message(store, "u1", second)
        assert store["u1"]["messages"][1] is first and len(store["u1"]["messages"]) == 3
        assert raises(ValueError, delete_message, store, "u1", store["u1"]["messages"][0])
        assert raises(ValueError, delete_message, store, "u1", {"role": "user", "content": "ok"})
        fork_session(store, "u1", "u1-b")
        add_message(store, "u1-b", "user", "only in the fork")
        store["u1-b"]["messages"][1]["content"] = "changed in fork"
        store["u1-b"]["settings"]["llm"]["temperature"] = 1.5
        assert [m["content"] for m in store["u1"]["messages"]] == ["Be brief.", "ok", "Noted."]
        assert store["u1"]["settings"]["llm"]["temperature"] == 0.2
        assert raises(ValueError, fork_session, store, "u1", "u2")
        """,
        hints=["`start_session`: build settings with `copy.deepcopy(DEFAULTS)`, then merge each nested dict of `settings` into its copy (2.3, problem 10 has a recursive version).",
               "`get_history`: a new list of new message dicts (2.3, problem 4).",
               "`delete_message`: find the position with `is` (2.1, problem 15), and treat position 0 as the system message.",
               "`fork_session`: `copy.deepcopy` of the whole session is right here: you want everything independent, and the session is small."],
        solution="""
        import copy

        DEFAULTS = {"llm": {"model": "small", "temperature": 0.2}, "tags": ["chat"]}


        def start_session(store, session_id, system, settings=None):
            if session_id in store:
                raise ValueError(f"session {session_id!r} already exists")
            merged = copy.deepcopy(DEFAULTS)
            for key, value in (settings or {}).items():
                if isinstance(merged.get(key), dict) and isinstance(value, dict):
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = copy.deepcopy(value)
            store[session_id] = {
                "messages": [{"role": "system", "content": system}],
                "settings": merged,
            }


        def add_message(store, session_id, role, content):
            msg = {"role": role, "content": content}
            store[session_id]["messages"].append(msg)
            return msg


        def get_history(store, session_id):
            return [dict(m) for m in store[session_id]["messages"]]


        def delete_message(store, session_id, msg):
            messages = store[session_id]["messages"]
            for i, m in enumerate(messages):
                if m is msg:
                    if i == 0:
                        raise ValueError("the system message cannot be deleted")
                    del messages[i]
                    return
            raise ValueError("message is not in this session")


        def fork_session(store, source_id, new_id):
            if new_id in store:
                raise ValueError(f"session {new_id!r} already exists")
            store[new_id] = copy.deepcopy(store[source_id])
        """,
        why="""Every function uses a different tool from the module:

        - `start_session` deep-copies `DEFAULTS` so no session shares its nested `llm` dict or `tags` list with the
          defaults or with other sessions (2.2, 2.3). The `None` default for `settings` avoids a shared default dict
          (2.4), and `settings or {}` is safe here because an empty dict and `None` both mean "no overrides". Values taken
          from `settings` are deep-copied too, so a caller who changes their own dict later cannot reach into the session.
        - `add_message` returns the stored object on purpose: callers use it as a handle for `delete_message`.
        - `get_history` copies two levels, exactly as deep as the data (2.3): a new list and a new dict per message.
        - `delete_message` searches by identity, so an equal message (the second "ok", or an outside copy) is never
          deleted by mistake (2.1).
        - `fork_session` is the one place where a full `deepcopy` is the right tool: the goal is total independence and
          sessions are small.

        A production version would store messages in a database with real ids instead of using object identity, lock
        sessions for concurrent requests (Module 14) and validate settings with Pydantic (Module 11). The ownership rules
        stay exactly the same."""),
)

recap(
    "Name the relationship first: alias, shallow copy or deep copy. Most Module 2 bugs are one of the three in the wrong place.",
    "Value questions use `==`, identity questions use `is`. Many real functions need both: decide by value, keep the original object.",
    "Copy as deep as the data needs and no deeper. Deep copies fix aliasing but cost time and hide the real design question: who may change this?",
    "Functions get your actual objects: pure by default, in place only when explicit, `None` or immutable defaults.",
)
