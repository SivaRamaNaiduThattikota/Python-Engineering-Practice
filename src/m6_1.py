from lesson import *

lesson(
    id="m6-1", num="6.1", title="List comprehensions",
    intro="A list comprehension builds a list from another iterable in one expression. What it translates to, filtering "
          "versus transforming, several `for` clauses, its own scope, why it is fast, and when a plain loop is the better "
          "choice. Applied to batching, message building, feature extraction and chunking.",
    desc="Transform and filter with `[expr for x in xs if cond]`, nested `for`, scope and speed.",
    keys="list comprehension comprehension filter transform conditional expression ternary nested for flatten scope walrus late binding lambda batch one hot sliding window",
)

term("List comprehension", "An expression like `[f(x) for x in xs if cond(x)]` that builds a new list by looping, filtering and transforming in one step.")
term("Conditional expression", "`a if cond else b`: an expression that picks one of two values. In a comprehension it goes at the front and transforms every item.")
term("Flatten", "Turn a list of lists into one list of their items, for example `[x for row in rows for x in row]`.")

section("what", "What a comprehension is, and the loop it stands for",
    p("""A **list comprehension** builds a new list by running an expression for every item of an iterable. The general shape
    is `[expression for name in iterable if condition]`, and it means exactly the same as this loop:"""),
    ex("""
    scores = [0.91, 0.42, 0.77, 0.15]

    # the loop
    kept = []
    for s in scores:
        if s >= 0.5:
            kept.append(round(s * 100))

    # the comprehension: the same three parts, in a different order
    kept2 = [round(s * 100) for s in scores if s >= 0.5]
    print(kept, kept2, kept == kept2)
    """, "loop_vs_comp.py"),
    p("""Read a comprehension in this order: first the `for` part (what you loop over and the name each item gets), then the
    `if` part (which items are kept), and last the expression at the front (what goes into the new list for each kept item).
    The expression comes first in the syntax because it is the most important thing: the result is "a list **of these**".
    Step by step, Python creates an empty list, takes each item of `scores` in order, binds it to `s`, evaluates the
    condition, and if it is true evaluates the expression and appends the result. The original list is never changed."""),
    p("""Any iterable works on the right: lists, tuples, strings, `range`, dict views, files (one line per item), and the
    generators of 6.3. The result is always a new `list`. The parts are optional except the first `for`: `[x * 2 for x in xs]`
    only transforms, `[x for x in xs if x]` only filters (it drops falsy items like `""`, `0` and `None`)."""),
    ex("""
    print([c.upper() for c in "rag"], [n * n for n in range(5)])
    print([w for w in ["a", "", "b", None, "c"] if w])
    totals = {"api": 12, "web": 0, "db": 7}
    print([name for name, n in totals.items() if n > 0])
    """, "any_iterable.py"),
    callout("sql", "SQL / Power BI", """A comprehension reads like a small `SELECT`: `[round(s * 100) for s in scores if s >= 0.5]`
    is `SELECT ROUND(s * 100) FROM scores WHERE s >= 0.5`. The expression is the select list, the `for` is the `FROM`, the
    `if` is the `WHERE`. In Power Query it is `Table.SelectRows` followed by `Table.TransformColumns`, and in DAX it is close to
    `SELECTCOLUMNS(FILTER(...), ...)`."""),
)

section("ifelse", "Filtering versus transforming: where the `if` goes",
    p("""There are two different `if`s, and mixing them up is the most common comprehension mistake. An `if` **at the end** is a
    filter: items that fail it are left out, so the result can be shorter than the input. An `if ... else` **at the front** is
    a conditional expression (`a if cond else b`): every item produces something, so the result has the same length as the
    input. A filter has no `else`; a conditional expression must have one."""),
    ex("""
    xs = [3, -1, 0, 5, -2]
    print([x for x in xs if x > 0])            # filter: shorter
    print([x if x > 0 else 0 for x in xs])     # transform: same length (ReLU)
    print(["pos" if x > 0 else "zero" if x == 0 else "neg" for x in xs])
    print([x * 10 if x % 2 else x for x in xs if x != 0])   # both at once
    """, "if_positions.py"),
    p("""The second line is the ReLU activation function from neural networks, written as a comprehension: negative values become
    0, the length is kept. Keeping the length matters whenever the list is aligned with another one, such as predictions and
    labels: filtering one of them silently misaligns every item after the first dropped one (problem 6)."""),
    p("""Conditional expressions can be chained, as the third line shows, but two levels is the readable limit; beyond that, put
    the logic in a small named function and call it from the comprehension. Two filters in a row, `if a if b`, mean `if a and
    b`. The syntax errors tell you which `if` you used wrongly: `[x if x > 0 for x in xs]` is a `SyntaxError` because a
    front-position `if` needs an `else`, and `[x for x in xs if x > 0 else 0]` is one because a filter cannot have an `else`."""),
    ex("""
    def label(score):
        if score >= 0.8:
            return "high"
        if score >= 0.5:
            return "medium"
        return "low"

    print([label(s) for s in [0.91, 0.42, 0.77, 0.15]])
    print([n for n in range(20) if n % 2 if n % 3])     # odd and not divisible by 3
    for bad in ["[x if x > 0 for x in xs]", "[x for x in xs if x > 0 else 0]"]:
        try:
            compile(bad, "<demo>", "eval")
        except SyntaxError as e:
            print("SyntaxError:", e.msg)
    """, "if_rules.py"),
)

section("nested", "Several `for` clauses, and comprehensions inside comprehensions",
    p("""A comprehension can have more than one `for`. They nest **left to right, in the same order as written loops**: the first
    `for` is the outer loop, the next one is inside it. So `[(a, b) for a in "xy" for b in "12"]` is the loop `for a in "xy":`
    with `for b in "12":` inside, producing `x1, x2, y1, y2`. A later `for` can use the name of an earlier one, which is how
    you **flatten** a list of lists: `[x for row in rows for x in row]` ("for each row, for each x in that row")."""),
    ex("""
    print([a + b for a in "xy" for b in "12"])
    docs = [["refund", "policy"], ["reset", "password", "now"], []]
    print([w for doc in docs for w in doc])
    print([w for doc in docs if len(doc) > 2 for w in doc if w != "now"])
    flat = []
    for doc in docs:           # the same as the second line, as loops
        for w in doc:
            flat.append(w)
    print(flat)
    """, "multi_for.py"),
    p("""A trick for the order: write the loops as normal nested loops first, then move the innermost body (`flat.append(w)`) to
    the front, and keep the `for` and `if` lines in their original order. Putting the `for`s the other way round, `[w for w in
    doc for doc in docs]`, fails because `doc` is used before the loop that defines it."""),
    p("""Different again is a comprehension **inside** the expression of another, which builds a list of lists: `[[r * c for c in
    range(3)] for r in range(3)]` builds a 3 x 3 table, one inner list per row. This is how you create a grid correctly.
    The tempting `[[0] * 3] * 3` does not work: `*` repeats **references** to one inner list (2.2), so all three rows are the
    same object and changing one changes them all (problem 3)."""),
    ex("""
    table = [[r * c for c in range(3)] for r in range(3)]
    print(table)
    matrix = [[1, 2, 3], [4, 5, 6]]
    print([[row[i] for row in matrix] for i in range(3)])     # transpose
    bad = [[0] * 3] * 3
    good = [[0] * 3 for _ in range(3)]
    bad[0][0] = 9
    good[0][0] = 9
    print(bad, good)
    """, "nested_comp.py"),
    p("""Use `_` as the loop name when the value is not needed, as in `for _ in range(3)`: it tells the reader the loop only
    counts. Beyond two `for` clauses, or when nesting and filters combine, a written loop is usually clearer."""),
)

section("scope", "Scope: what a comprehension can see and leak",
    p("""A comprehension has its **own scope** for its loop variables. In Python 3 the name after `for` does not exist after the
    comprehension, and it does not overwrite a variable with the same name outside it. (In Python 2 it did leak, which is why
    old code avoided reusing names.) Everything else follows the normal rules of 3.3: the expression and conditions can read
    variables from the enclosing function and module."""),
    ex("""
    x = "outer"
    squares = [x * x for x in range(4)]
    print(squares, x)
    threshold = 2
    print([n for n in range(5) if n > threshold])     # reads the enclosing name
    try:
        print(n)
    except NameError as e:
        print("NameError:", e)
    """, "comp_scope.py"),
    p("""Two scope details matter in real code. The **walrus operator** `:=` inside a comprehension binds its name in the
    **enclosing** scope, on purpose, so you can compute a value once, use it in both the filter and the expression, and still
    see the last value afterwards. And because the loop variable is looked up when a function **runs**, not when it is
    created, `[lambda: i for i in range(3)]` builds three functions that all see the **last** `i`: the late-binding closure of
    3.4. The fix is the same as there: bind the current value as a default argument, `lambda i=i: i` (problem 10)."""),
    ex("""
    texts = ["  refund  ", "", "reset password ", "   "]
    cleaned = [t for raw in texts if (t := raw.strip())]
    print(cleaned, repr(t))
    fns = [lambda: i for i in range(3)]
    fixed = [lambda i=i: i for i in range(3)]
    print([f() for f in fns], [f() for f in fixed])
    """, "walrus_and_lambdas.py"),
    p("""In the first line, `raw.strip()` runs once per item: its result is bound to `t`, tested in the filter, and reused in the
    expression. Without the walrus you would write `[raw.strip() for raw in texts if raw.strip()]` and strip every item
    twice."""),
)

section("speed", "Speed: what is true today, and what comprehensions cost",
    p("""You will often read that comprehensions are much faster than a loop with `append`. The reason is real: the loop looks up
    `result.append` on every iteration and makes a method call, while the comprehension compiles to a dedicated bytecode
    instruction, `LIST_APPEND`, that adds to the list directly. On older Pythons that saved 20 to 50 percent for simple
    expressions. But since Python 3.11 the interpreter **specialises** hot code while it runs, and it recognises
    `some_list.append(x)` and turns it into a fast path; Python 3.12 also inlines comprehensions into the enclosing function.
    Measured on this page's Python 3.14, squaring a million integers takes nearly the same time either way (a few percent
    apart). The lesson is the general one: performance folklore goes out of date, so measure on the version you run."""),
    p("""So choose a comprehension for **clarity**: it says "build a list of these" in one expression, with no half-built list
    visible to the rest of the function. The big speed differences come from elsewhere: doing less work (stopping early, as
    below), using a better data structure (4.4, 4.5), or moving numeric work into NumPy, which runs the whole loop in C."""),
    ex("""
    import dis

    def with_loop(xs):
        out = []
        for x in xs:
            out.append(x * 2)
        return out

    def with_comp(xs):
        return [x * 2 for x in xs]

    def ops(f):
        return {i.opname for i in dis.get_instructions(f)}

    print("LIST_APPEND" in ops(with_comp), "LIST_APPEND" in ops(with_loop))
    print(with_loop([1, 2]) == with_comp([1, 2]))
    """, "bytecode.py"),
    p("""The real cost of a list comprehension is **memory**: it builds the whole list at once. That is fine for thousands or millions of
    small items, but not for a 50 GB file, and it is wasteful when you only need one pass over the results, such as a sum or
    an `any` check. Replacing the square brackets with parentheses gives a **generator expression**, which produces items one
    at a time without storing them (6.3). With `any` and `all` it also **stops early**: the list version computes every item
    first, the generator version stops at the first true one."""),
    ex("""
    calls = 0

    def is_long(text):
        global calls
        calls += 1
        return len(text) > 10

    docs = ["short", "a very long document", "x", "y", "z"]
    print(any([is_long(d) for d in docs]), calls)
    calls = 0
    print(any(is_long(d) for d in docs), calls)
    print(sum(len(d) for d in docs))
    """, "comp_vs_genexp.py"),
    p("""`map` and `filter` do the same jobs (`list(map(str.upper, words))`), and they can be slightly faster when the function
    is a C built-in, but a comprehension is clearer as soon as you need a `lambda` or both filtering and transforming."""),
)

section("when", "When to use a comprehension, and when not",
    p("""Use a comprehension when you are **building a list from another iterable** with one expression and at most a simple
    filter. That covers a large share of everyday data code: selecting fields, cleaning values, filtering results, batching,
    building prompts and messages. Use a written loop when:"""),
    p("""- the body has **several statements**, `try` / `except`, or early exits (`break`, `return`);
    - you need **side effects**, such as printing, logging or writing to a database: `[print(x) for x in xs]` builds a list of
      `None` values just to throw it away, and hides the side effect in an expression;
    - the comprehension would need more than two `for` clauses or chained conditions that no longer read as one sentence;
    - you are **updating** existing objects rather than building new values."""),
    ex("""
    texts = ["Refunds take 5 days.", "Reset your password here.", "OK"]
    batch_size = 2
    batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
    print(batches)
    history = [("user", "Hi"), ("assistant", "Hello!"), ("user", "Refund?")]
    messages = [{"role": role, "content": text} for role, text in history]
    print(messages[-1])
    features = [[len(t), t.count(" ") + 1, t.endswith("?")] for t in texts]
    print(features)
    """, "in_practice.py"),
    p("""These three are the most common comprehensions in GenAI and ML code. **Batching** with `range(0, n, size)` and slices
    sends texts to an embedding API in groups that respect its limit (slices never fail, so the last batch is simply shorter).
    **Message building** turns stored chat history into the list of dicts that chat APIs expect. **Feature extraction** turns
    each text into a row of numbers, the list-of-lists shape that scikit-learn accepts as `X`."""),
)

section("warmup", "Warm-up",
    predict("Reading comprehensions", "easy",
        code="""
        xs = [4, -2, 0, 7, -5]
        print([x for x in xs if x])
        print([x if x > 0 else 0 for x in xs])
        print([str(x) for x in xs if x < 0], [c * 2 for c in "ab"])
        x = 100
        print([x + 1 for x in range(3)], x)
        """,
        hints=["An `if` at the end filters; `if ... else` at the front transforms every item. The comprehension's `x` is its own."],
        why="""`if x` drops the falsy `0`. The conditional expression keeps the length and turns negatives into 0. The third line
        filters and then transforms the survivors into strings; strings are iterables of characters. The comprehension's `x`
        lives in its own scope, so the outer `x = 100` is untouched."""),
    write("Batch texts for an embedding API", "easy", tag="GenAI",
        prompt="""Embedding APIs limit how many texts one request can carry. Write `batches(texts, size)` returning a list of
        lists of at most `size` texts each, in order, using one list comprehension. Raise `ValueError` if `size` is less than
        1.""",
        code="""
        def batches(texts, size):
            pass
        """,
        tests="""
        texts = [f"t{i}" for i in range(7)]
        assert batches(texts, 3) == [["t0", "t1", "t2"], ["t3", "t4", "t5"], ["t6"]]
        assert batches(texts, 10) == [texts]
        assert batches([], 4) == []
        try:
            batches(texts, 0)
            assert False, "size 0 should raise"
        except ValueError:
            pass
        """,
        hints=["`range(0, len(texts), size)` gives the start of each batch; slice from there."],
        solution="""
        def batches(texts, size):
            if size < 1:
                raise ValueError("size must be at least 1")
            return [texts[i:i + size] for i in range(0, len(texts), size)]
        """,
        why="""The `range` step jumps from one batch start to the next, and the slice takes up to `size` items, shorter at the end
        because slicing past the end is safe (4.1). With an empty list, `range(0, 0, size)` is empty, so the result is `[]`.
        The check for `size` comes first because `range` with a step of 0 raises its own, less helpful, `ValueError`, and a
        negative step would silently return nothing. `itertools.batched` (Python 3.12+, 6.4) does the same lazily."""),
    fix("A grid where every row changes together", "easy", tag="Data work",
        prompt="""`empty_grid(rows, cols)` builds a confusion-matrix grid of zeros. Updating one cell changes the whole column.
        Fix it.""",
        code="""
        def empty_grid(rows, cols):
            return [[0] * cols] * rows
        """,
        tests="""
        g = empty_grid(3, 2)
        g[0][1] += 1
        assert g == [[0, 1], [0, 0], [0, 0]]
        assert empty_grid(0, 4) == []
        assert len({id(row) for row in empty_grid(4, 1)}) == 4
        """,
        hints=["`* rows` repeats the same inner list object. Build a new inner list for each row with a comprehension."],
        solution="""
        def empty_grid(rows, cols):
            return [[0] * cols for _ in range(rows)]
        """,
        why="""`[inner] * rows` makes a list of `rows` references to **one** inner list (2.2), so `g[0]`, `g[1]` and `g[2]` are the
        same object. The comprehension evaluates `[0] * cols` once per iteration, creating a new list each time. The inner
        `[0] * cols` is fine, because it repeats an immutable `0`. The last test checks identity directly: four rows, four
        distinct objects."""),
    predict("Several `for` clauses", "easy",
        code="""
        print([a + b for a in "ab" for b in "xyz"])
        rows = [[1, 2], [3], [], [4, 5, 6]]
        print([x for row in rows for x in row])
        print([x for row in rows if len(row) > 1 for x in row if x % 2 == 0])
        print([[x * 10 for x in row] for row in rows if row])
        """,
        hints=["The first `for` is the outer loop. A comprehension in the expression builds one inner list per outer item."],
        why="""`for a` is the outer loop, so all of `a`'s pairs come before `b`'s. The second line flattens. The third filters rows
        (two rows have more than one item), then filters items inside them (the even ones). The last line keeps the nested shape:
        the inner comprehension runs once per non-empty row and produces one list for each."""),
)

section("medium", "Medium",
    write("Keep the best retrieved chunks", "medium", tag="RAG",
        prompt="""A retriever returns results as dicts with `"text"`, `"score"` and `"source"`. Write `context_chunks(results,
        min_score, limit)` returning the texts (stripped) of results with `score >= min_score`, best score first, at most
        `limit` of them, dropping results whose text is empty after stripping. Use comprehensions.""",
        code="""
        def context_chunks(results, min_score, limit):
            pass
        """,
        tests="""
        results = [
            {"text": " Refunds take 5 days. ", "score": 0.82, "source": "faq"},
            {"text": "Office hours", "score": 0.31, "source": "misc"},
            {"text": "   ", "score": 0.95, "source": "empty"},
            {"text": "No refunds after 30 days.", "score": 0.91, "source": "terms"},
            {"text": "Refund form link", "score": 0.66, "source": "faq"},
        ]
        assert context_chunks(results, 0.5, 2) == ["No refunds after 30 days.", "Refunds take 5 days."]
        assert context_chunks(results, 0.5, 10) == ["No refunds after 30 days.", "Refunds take 5 days.", "Refund form link"]
        assert context_chunks(results, 0.99, 3) == []
        assert context_chunks([], 0.0, 3) == []
        """,
        hints=["Filter first: `[r for r in results if r[\"score\"] >= min_score and r[\"text\"].strip()]`.",
               "Then sort the survivors by score, descending, slice to `limit`, and take the stripped texts."],
        solution="""
        def context_chunks(results, min_score, limit):
            good = [r for r in results if r["score"] >= min_score and r["text"].strip()]
            good.sort(key=lambda r: r["score"], reverse=True)
            return [r["text"].strip() for r in good[:limit]]
        """,
        why="""Each step is one simple operation: filter, sort, cut, project. Filtering before sorting means less to sort. Checking
        `r["text"].strip()` in the filter drops the whitespace-only result even though it has the best score, which is a real
        failure mode: a high-scoring empty chunk wastes a context slot. Sorting the filtered dicts (rather than the texts) keeps the
        score available as the key (4.2). The same filter-sort-limit shape appears in every RAG pipeline before the prompt is
        built."""),
    fix("ReLU that drops values", "medium", tag="ML",
        prompt="""`relu(xs)` should replace negative values with 0 and keep the rest, so the output lines up with the input. The
        code drops the negatives instead, and predictions no longer align with labels. Fix it.""",
        code="""
        def relu(xs):
            return [x for x in xs if x > 0]
        """,
        tests="""
        assert relu([1.5, -2.0, 0.0, 3.0]) == [1.5, 0.0, 0.0, 3.0]
        assert len(relu([-1] * 5)) == 5
        assert relu([]) == []
        """,
        hints=["You need a value for every item: a conditional expression at the front, not a filter at the end."],
        solution="""
        def relu(xs):
            return [x if x > 0 else 0.0 for x in xs]
        """,
        why="""A filter changes the length; a conditional expression at the front keeps it, producing one value per input. Whenever a
        list is aligned with another (features and labels, predictions and ids), filtering one of them shifts every later item,
        and the error shows up far away as nonsense metrics rather than as an exception. `max(x, 0.0)` is an equivalent
        expression. In NumPy this is `np.maximum(xs, 0)`, done on the whole array at once."""),
    write("Chat history to API messages", "medium", tag="GenAI",
        prompt="""Your app stores chat history as `(speaker, text)` tuples, with speakers `"user"`, `"bot"` and `"system"`.
        Write `to_messages(history, system_prompt)` returning the list of dicts a chat API expects: the system prompt first as
        `{"role": "system", "content": ...}`, then each stored turn with `"bot"` renamed to `"assistant"`, stripped text, skipping
        turns whose text is empty and skipping stored `"system"` turns (the new system prompt replaces them).""",
        code="""
        def to_messages(history, system_prompt):
            pass
        """,
        tests="""
        history = [("system", "old prompt"), ("user", " Hi "), ("bot", "Hello!"), ("user", "   "), ("user", "Refund?")]
        assert to_messages(history, "Be brief.") == [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Refund?"},
        ]
        assert to_messages([], "S") == [{"role": "system", "content": "S"}]
        """,
        hints=["A small dict `{\"bot\": \"assistant\"}` with `.get(speaker, speaker)` renames roles.",
               "Use the walrus to strip once: `if speaker != \"system\" and (text := raw.strip())`."],
        solution="""
        ROLES = {"bot": "assistant"}

        def to_messages(history, system_prompt):
            turns = [
                {"role": ROLES.get(speaker, speaker), "content": text}
                for speaker, raw in history
                if speaker != "system" and (text := raw.strip())
            ]
            return [{"role": "system", "content": system_prompt}] + turns
        """,
        why="""Unpacking `speaker, raw` in the `for` clause names the tuple parts (4.3). The walrus strips each text once and makes it
        available to both the filter and the expression; the `and` short-circuits, so system turns are not even stripped. A
        lookup dict with `.get(key, key)` renames only what needs renaming and passes everything else through (4.5). Splitting a
        long comprehension over several lines, one clause per line, keeps it readable. This conversion layer is where chat apps
        keep their storage format independent of any one provider's API."""),
    choose("Is any score above the threshold: brackets or not", "medium",
        prompt="Both check whether any of 1,000,000 scores is above 0.9. The first such score is near the start. Which is faster?",
        setup="""scores = [0.1] * 20 + [0.95] + [0.2] * 999_979""",
        options={
            "a": "found = any([s > 0.9 for s in scores])",
            "b": "found = any(s > 0.9 for s in scores)",
        },
        answer="b",
        hints=["How many comparisons does each version make before `any` can answer?"],
        why="""The square brackets build the full list of one million booleans first, and only then does `any` look at it. The generator
        expression hands `any` one value at a time, and `any` stops at the first `True`, here after 21 comparisons. The two
        brackets look like a small style choice, but they change the amount of work from "all items" to "until the answer is
        known". The same holds for `all` (stops at the first `False`) and for `next(x for x in xs if cond)`, which finds the
        first match. When the match is at the end, or there is none, both do all the work and the difference becomes small."""),
    trace("Comprehensions step by step", "medium",
        prompt="Fill in `r` after each marked line.",
        code="""
        words = ["Refund", "", "policy", "EU", "  "]
        r = [w.lower() for w in words if w.strip()]  # row: "clean and filter"
        r = [len(w) for w in r]  # row: "lengths"
        r = [n if n > 2 else -n for n in r]  # row: "conditional"
        r = [(i, n) for i, n in enumerate(r) if n > 0]  # row: "enumerate and filter"
        r = [x for pair in r for x in pair]  # row: "flatten"
        """,
        trace_vars=["r"],
        hints=["Each line uses the previous `r`. `enumerate` numbers the items from 0."],
        why="""The first line drops the empty and whitespace-only words and lower-cases the rest. Lengths are then 6, 6 and 2. The
        conditional expression keeps the length of the list, negating the 2. The filter after `enumerate` keeps the original
        positions of the survivors, which is how you remember where a kept item came from. The last line flattens the pairs into
        one list."""),
    fix("Scalers that all use the last factor", "medium", tag="ML",
        prompt="""`make_scalers(factors)` should return one function per factor, each multiplying its input by that factor.
        Every function multiplies by the last factor. Fix it.""",
        code="""
        def make_scalers(factors):
            return [lambda x: x * f for f in factors]
        """,
        tests="""
        double, triple, half = make_scalers([2, 3, 0.5])
        assert (double(10), triple(10), half(10)) == (20, 30, 5.0)
        assert make_scalers([]) == []
        """,
        hints=["The lambda looks up `f` when it is called, after the comprehension has finished. Capture the current value as a default argument."],
        solution="""
        def make_scalers(factors):
            return [lambda x, f=f: x * f for f in factors]
        """,
        why="""All three lambdas close over the same variable `f` of the comprehension's scope, and they read it when called, by which
        time the loop has finished and `f` is `0.5`: late binding (3.4). A default argument is evaluated when the lambda is
        **created**, so `f=f` stores each current value in its own function. `functools.partial(operator.mul, f)` is an
        alternative that avoids the trick. The same bug appears when building callbacks or tools in a loop."""),
    refactor("Nested loops to a comprehension", "medium", tag="Data work",
        prompt="Rewrite with one list comprehension, same result. Keep the tests green.",
        code="""
        def long_sentences(docs, min_words):
            out = []
            for doc in docs:
                if doc["lang"] != "en":
                    continue
                for sentence in doc["text"].split(". "):
                    sentence = sentence.strip(" .")
                    if len(sentence.split()) >= min_words:
                        out.append((doc["id"], sentence))
            return out
        """,
        tests="""
        docs = [
            {"id": "a", "lang": "en", "text": "Refunds take 5 days. Ok. Contact support for help."},
            {"id": "b", "lang": "de", "text": "Rückerstattung dauert 5 Tage."},
            {"id": "c", "lang": "en", "text": "Reset your password from the login page."},
        ]
        assert long_sentences(docs, 3) == [("a", "Refunds take 5 days"), ("a", "Contact support for help"),
                                           ("c", "Reset your password from the login page")]
        assert long_sentences([], 1) == []
        """,
        hints=["Keep the loop order: `for doc in docs if ...` then `for raw in doc[\"text\"].split(\". \")`.",
               "The `sentence = sentence.strip(\" .\")` step can become a walrus in the last filter: `if len((s := raw.strip(\" .\")).split()) >= min_words`."],
        solution="""
        def long_sentences(docs, min_words):
            return [
                (doc["id"], s)
                for doc in docs
                if doc["lang"] == "en"
                for raw in doc["text"].split(". ")
                if len((s := raw.strip(" .")).split()) >= min_words
            ]
        """,
        why="""The clauses appear in exactly the order of the loops: the `continue` becomes a filter on `doc`, the inner loop becomes the
        second `for`, and the reassignment of `sentence` becomes a walrus inside the last filter, so the stripped text is computed
        once and used in the expression. This is about the limit of what a comprehension should hold; one more condition or
        transformation and the written loop would be the better choice."""),
    predict("Comprehensions that stop early, and those that do not", "medium",
        code="""
        seen = []

        def check(x):
            seen.append(x)
            return x > 2

        print(any([check(x) for x in [1, 3, 5, 7]]), seen)
        seen.clear()
        print(any(check(x) for x in [1, 3, 5, 7]), seen)
        seen.clear()
        print(all(check(x) for x in [3, 1, 5]), seen)
        print(type([x for x in "ab"]).__name__, type((x for x in "ab")).__name__)
        """,
        hints=["The list comprehension is fully built before `any` sees it. The generator expression produces one value at a time."],
        why="""With square brackets, the whole list is computed first, so `check` runs on all four items. With parentheses, `any`
        pulls values one at a time and stops at the first true one (3), so `check` ran twice. `all` stops at the first false one
        (1). The parentheses give a `generator` object, not a tuple; 6.3 explains how it works. For `any`, `all`, `sum`, `min`
        and `max`, the generator form is the default choice."""),
)

section("hard", "Hard",
    write("One-hot encode labels", "hard", tag="ML",
        prompt="""Write `one_hot(labels, classes)` returning one row per label, each a list of `0`s with a `1` at the position of
        that label in `classes`. Raise `ValueError` naming the unknown labels (sorted) if any label is not in `classes`. Build the
        rows with a nested comprehension.""",
        code="""
        def one_hot(labels, classes):
            pass
        """,
        tests="""
        assert one_hot(["spam", "ham", "spam"], ["ham", "spam"]) == [[0, 1], [1, 0], [0, 1]]
        assert one_hot([], ["a"]) == []
        assert one_hot(["b"], ["a", "b", "c"]) == [[0, 1, 0]]
        try:
            one_hot(["ham", "eggs", "bacon"], ["ham", "spam"])
            assert False, "should raise"
        except ValueError as e:
            assert "bacon" in str(e) and "eggs" in str(e) and str(e).index("bacon") < str(e).index("eggs")
        """,
        hints=["Check first: `unknown = sorted(set(labels) - set(classes))`.",
               "Then `[[1 if c == label else 0 for c in classes] for label in labels]`, or `int(c == label)`."],
        solution="""
        def one_hot(labels, classes):
            unknown = sorted(set(labels) - set(classes))
            if unknown:
                raise ValueError(f"unknown labels: {unknown}")
            return [[int(c == label) for c in classes] for label in labels]
        """,
        why="""Validation comes first, with set difference (4.4), so the function fails with a clear message instead of producing a row
        of all zeros that a model would silently learn from. The nested comprehension builds one inner list per label; inside it,
        `int(c == label)` turns the `True`/`False` comparison into `1`/`0`. Each row is compared against every class, which is
        O(labels x classes); for many classes, build an index dict once (4.5) and set one position per row. scikit-learn's
        `OneHotEncoder` and `pandas.get_dummies` do this on whole columns."""),
    write("Overlapping windows for chunking", "hard", tag="RAG",
        prompt="""RAG pipelines often cut token lists into overlapping windows so a sentence at a boundary appears whole in at
        least one chunk. Write `windows(tokens, size, overlap)` returning windows of `size` tokens, each starting `size -
        overlap` after the previous one. If the last regular window does not reach the end, add one final window made of the
        last `size` tokens. If there are `size` tokens or fewer, return one window with all of them (none for an empty list).
        Raise `ValueError` unless `0 <= overlap < size`.""",
        code="""
        def windows(tokens, size, overlap):
            pass
        """,
        tests="""
        t = list(range(10))
        assert windows(t, 4, 1) == [[0, 1, 2, 3], [3, 4, 5, 6], [6, 7, 8, 9]]
        assert windows(t, 4, 2) == [[0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 7], [6, 7, 8, 9]]
        assert windows(t, 6, 0) == [[0, 1, 2, 3, 4, 5], [4, 5, 6, 7, 8, 9]]
        assert windows(t[:3], 5, 1) == [[0, 1, 2]]
        assert windows([], 5, 1) == []
        for bad in [(4, 4), (4, -1)]:
            try:
                windows(t, *bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["The starts of the regular windows are `range(0, len(tokens) - size + 1, size - overlap)`.",
               "After building them, compare the last window's end (`start + size`) with `len(tokens)` and append `tokens[-size:]` if it falls short."],
        solution="""
        def windows(tokens, size, overlap):
            if not 0 <= overlap < size:
                raise ValueError("need 0 <= overlap < size")
            if len(tokens) <= size:
                return [list(tokens)] if tokens else []
            step = size - overlap
            starts = range(0, len(tokens) - size + 1, step)
            out = [tokens[s:s + size] for s in starts]
            if starts[-1] + size < len(tokens):
                out.append(tokens[-size:])
            return out
        """,
        why="""The window starts form an arithmetic sequence, so a `range` with step `size - overlap` generates them, and its stop value
        `len - size + 1` makes the last regular window end exactly at or before the end. A `range` supports indexing, so
        `starts[-1]` gives the last start without building a list. When the step does not divide evenly (the third test), the
        final window is aligned to the end, which overlaps the previous one more than requested but never drops tokens and never
        produces a short chunk. `overlap >= size` would make the step 0 or negative, so it is rejected first. Libraries such as
        LangChain's `TokenTextSplitter` use this scheme with `chunk_size` and `chunk_overlap`."""),
    fix("Read the code: a document-term matrix", "hard", tag="ML",
        prompt="""This builds a bag-of-words matrix: a vocabulary of words that occur at least `min_count` times across all
        documents, and one row of word counts per document. It crashes, and after fixing the crash the counts are wrong. Read it,
        find the bugs and fix them. Words are lower-cased, with `.,!?` stripped from their ends.""",
        code="""
        def doc_term_matrix(docs, min_count=1):
            tokens = [w.strip(".,!?") for w in doc.lower().split() for doc in docs]
            counts = {}
            [counts.update({w: counts.get(w, 0) + 1}) for w in tokens]
            vocab = sorted(w for w in counts if counts[w] >= min_count)
            index = {}
            for i, w in enumerate(vocab):
                index[w] = i
            matrix = [[0] * len(vocab)] * len(docs)
            for d, doc in enumerate(docs):
                for w in doc.lower().split():
                    w = w.strip(".,!?")
                    if w in index:
                        matrix[d][index[w]] += 1
            return vocab, matrix
        """,
        tests="""
        docs = ["Refund now!", "Refund, refund policy.", "Policy update"]
        vocab, m = doc_term_matrix(docs)
        assert vocab == ["now", "policy", "refund", "update"]
        assert m == [[1, 0, 1, 0], [0, 1, 2, 0], [0, 1, 0, 1]]
        vocab, m = doc_term_matrix(docs, min_count=2)
        assert vocab == ["policy", "refund"] and m == [[0, 1], [1, 2], [1, 0]]
        assert doc_term_matrix([]) == ([], [])
        """,
        hints=["The `for` clauses of the first comprehension are in the wrong order: `doc` is used before the loop that defines it.",
               "`[[0] * len(vocab)] * len(docs)` repeats one row object.",
               "The `[counts.update(...) for w in tokens]` line works, but it builds a throwaway list of `None`s for a side effect. Use a plain loop or `Counter` (4.6)."],
        solution="""
        from collections import Counter


        def doc_term_matrix(docs, min_count=1):
            tokens = [w.strip(".,!?") for doc in docs for w in doc.lower().split()]
            counts = Counter(tokens)
            vocab = sorted(w for w in counts if counts[w] >= min_count)
            index = {}
            for i, w in enumerate(vocab):
                index[w] = i
            matrix = [[0] * len(vocab) for _ in docs]
            for d, doc in enumerate(docs):
                for w in doc.lower().split():
                    w = w.strip(".,!?")
                    if w in index:
                        matrix[d][index[w]] += 1
            return vocab, matrix
        """,
        why="""Bug one: `for w in doc.lower().split() for doc in docs` puts the inner loop first. The first `for` is evaluated in the
        function's scope, where `doc` is a local assigned only later by the `enumerate` loop, so it raises `UnboundLocalError`.
        The `for` clauses must be in the order of written nested loops. Bug two: the matrix rows were one shared list, so every
        document's counts were added into the same row and every row showed the total. A comprehension creates one row per
        document. The side-effect comprehension was not a bug, but it is a code smell: it builds a list of `None` only to discard
        it; `Counter(tokens)` says what it means. The tokenising rule is written twice (once for the vocabulary, once for the
        rows), which is the next thing to refactor into one function. scikit-learn's `CountVectorizer` produces the same matrix,
        stored sparsely."""),
    predict("Scope, walrus and two filters", "hard",
        code="""
        i = "outer"
        data = [3, 8, 1, 9, 4]
        big = [y for x in data if (y := x * 2) > 6]
        print(big, y, i)
        print([i for i in range(10) if i % 2 if i % 3], i)
        pairs = [(i, j) for i in range(3) for j in range(i)]
        print(pairs)
        print([[j for j in range(i)] for i in range(4)])
        """,
        hints=["The walrus binds in the enclosing scope, so `y` exists afterwards. The loop variable `i` does not leak.",
               "In `for j in range(i)`, the inner range depends on the outer `i`."],
        why="""The walrus runs for **every** item, before the filter decides, and binds `y` in the enclosing scope, so afterwards `y`
        holds the value from the last item processed, `4 * 2 = 8`, whether or not that item passed the filter. The comprehension's `i` is separate from the outer `i`, which still holds `"outer"`. Two filters mean both must be
        true: odd and not divisible by 3. In `for j in range(i)` the inner loop depends on the outer one, producing pairs below
        the diagonal, and the nested comprehension produces lists of growing length, one per outer `i`."""),
)

section("interview", "Interview questions",
    explain("When would you use a list comprehension, a generator expression, `map`/`filter`, or a plain loop?", "medium", tag="Interview",
        why="""A **list comprehension** when you need the whole list (to index it, iterate it more than once, or return it) and the logic
        is one expression with at most a simple filter. A **generator expression** when you consume the values once, especially
        inside `sum`, `any`, `all`, `max`, `"".join` or a `for` loop, and for large or unbounded data, since it produces items
        lazily without storing them, and `any`/`all` can stop early. **`map`/`filter`** when you already have a named function,
        especially a built-in (`map(str.strip, lines)`); with a `lambda`, a comprehension is clearer. A **plain loop** when the
        body has several statements, error handling, early exit, or side effects, or when a comprehension would need more than two
        `for` clauses. Readability decides when performance is similar, which is most of the time."""),
    explain("Are list comprehensions faster than a loop with `append`? Why, and does it matter?", "medium", tag="Interview",
        why="""Historically yes, noticeably: the loop looks up the `append` attribute and makes a method call on every iteration, while
        the comprehension compiles to a dedicated `LIST_APPEND` bytecode. On modern CPython the gap is small: since 3.11 the
        specialising interpreter turns `list.append` calls into a fast path, and since 3.12 comprehensions are inlined into the
        enclosing function (PEP 709). A good answer says that, and adds that you would measure with `timeit` on the version you
        deploy. The saving is per item and fixed, so it disappears when each item does real work (parsing JSON, running a
        regex, calling a model). Choose comprehensions for clarity; for real speed-ups, do less work (early exit with a generator
        and `any`), pick a better data structure, or vectorise numeric work with NumPy or pandas."""),
    explain("A teammate loads a 50 GB JSON Lines file with `docs = [json.loads(line) for line in open(path)]`. What is wrong, and how would you fix it?", "hard", tag="Interview",
        why="""It materialises every parsed document in memory at once; Python objects are several times larger than the raw text, so
        this needs far more than 50 GB of RAM and will crash or swap. The file is also opened without `with` and without an
        explicit encoding (5.4). The fix is to **stream**: open the file in a `with` block with `encoding="utf-8"`, and process
        it with a generator expression or a generator function that yields one parsed document at a time, so memory stays
        constant (6.3). If work must be batched (for example embedding 256 documents per request), group the stream into
        batches lazily (`itertools.batched`, 6.4) and write results out as you go. For analytics on such files, tools like
        Polars or DuckDB scan JSON Lines lazily and in parallel. Also handle bad lines: wrap `json.loads` in `try` and count or
        log failures instead of losing the whole run to one corrupt line."""),
)

recap(
    "`[expr for x in xs if cond]` is a loop that appends `expr` for every `x` that passes `cond`. Read it `for`, then `if`, then the expression.",
    "An `if` at the end filters (shorter list); `a if c else b` at the front transforms every item (same length).",
    "Several `for` clauses nest left to right like written loops; a comprehension in the expression builds a list of lists. Never `[[0] * n] * m`.",
    "Loop variables do not leak, the walrus does on purpose, and lambdas created in a comprehension see the last value unless bound with a default.",
    "Comprehensions are fast but build the whole list. For one pass, `any`/`all` or large data, use a generator expression; for multi-step bodies and side effects, a loop.",
)
