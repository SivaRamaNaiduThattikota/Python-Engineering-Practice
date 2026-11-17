from lesson import *

lesson(
    id="m3-3", num="3.3", title="Scope: local, enclosing, global, built-in",
    intro="Where Python looks up a name, why assigning to a name anywhere in a function changes how it is read "
          "everywhere in that function, when `global` and `nonlocal` are needed, and why module-level state makes "
          "data and LLM code hard to test.",
    desc="The LEGB rule, `global`, `nonlocal`, and the UnboundLocalError trap.",
    keys="scope legb local enclosing global builtin namespace unboundlocalerror global nonlocal shadowing builtins module state comprehension scope class scope locals globals",
)

term("Scope", "The region of code where a name refers to a particular variable. Python has local, enclosing, global and built-in scopes.")
term("LEGB", "The order Python searches when it reads a name: Local, Enclosing, Global, Built-in. The first match wins.")
term("UnboundLocalError", "Raised when a function reads a local name before assigning it, usually because an assignment later in the function made the name local.")
term("Shadowing", "A name in an inner scope hiding the same name in an outer scope, such as a variable called `list` hiding the built-in.")

LEGB_FIG = """
<svg viewBox="0 0 640 170" role="img" aria-label="Four nested boxes: built-in contains global contains enclosing contains local. A name is looked up from the innermost box outwards.">
  <rect x="10" y="10" width="620" height="150" rx="16" class="box"/>
  <text x="26" y="32" class="h">Built-in   len, print, sum, range, ValueError ...</text>
  <rect x="40" y="42" width="560" height="108" rx="14" class="box"/>
  <text x="56" y="64" class="h">Global (module)   import json, MODEL = "small", def outer ...</text>
  <rect x="70" y="74" width="500" height="66" rx="12" class="box b"/>
  <text x="86" y="96" class="w">Enclosing (outer function)   prefix = "doc"</text>
  <rect x="300" y="102" width="250" height="30" rx="9" class="box a"/>
  <text x="425" y="122" class="w mid">Local (inner function)   i, text</text>
  <text x="225" y="125" class="w mid">look up: L, then E, then G, then B</text>
</svg>"""

section("legb", "Where Python looks for a name: LEGB",
    p("""A **scope** is the part of a program where a name refers to one particular variable. When Python reads a name,
    it searches scopes in a fixed order and uses the **first** match:"""),
    p("""- **L, Local:** names assigned inside the function that is running, including its parameters.
    - **E, Enclosing:** names in any function that contains this function (only for functions defined inside other
      functions).
    - **G, Global:** names assigned at the top level of the module (the file), including imports and `def`s.
    - **B, Built-in:** names Python provides everywhere, such as `len`, `print`, `range` and `ValueError`."""),
    fig(LEGB_FIG, "Each function call gets its own local scope. Lookup goes from the innermost scope outwards."),
    ex("""
    MODEL = "small"                       # global

    def outer():
        prefix = "doc"                    # local to outer, enclosing for inner
        def inner(i):
            text = f"{prefix}-{i}"        # i and text are local; prefix is found in E
            return text, MODEL, len(text) # MODEL found in G, len in B
        return inner(7)

    print(outer())
    """, "legb.py"),
    p("""Two details matter. A **new local scope is created on every call**, so locals from one call never leak into the
    next (that is why recursion works, 3.1). And only functions create scopes in Python: an `if` block or a `for` loop
    does **not**. A variable assigned inside a loop is a normal local of the surrounding function and is still visible
    after the loop (1.2)."""),
    callout("sql", "SQL / Power BI", """LEGB is like name resolution in nested SQL: a column name in a subquery is looked up
    in that subquery's own tables first, then in the outer query (a correlated subquery), and finally in what the database
    provides. In DAX, a `VAR` defined inside a measure hides a measure or column with the same name for the rest of that
    expression, just as a local hides a global."""),
)

section("assignment", "Assignment decides the scope, for the whole function",
    p("""Reading a name searches LEGB. **Assigning** works differently, and this is the part that causes real bugs. When
    Python **compiles** a function, it scans the whole body. Any name that is assigned **anywhere** in the function (with
    `=`, `+=`, a `for` target, an `import`, a `def` or `with ... as`) becomes a **local name for the entire function**,
    even on lines before the assignment."""),
    ex("""
    count = 10

    def read_only():
        return count + 1          # count is only read: found in G

    def broken():
        print("before:", count)   # count is assigned below, so it is LOCAL here too
        count = 0

    print(read_only())
    try:
        broken()
    except UnboundLocalError as e:
        print("UnboundLocalError:", e)
    """, "unbound_local.py"),
    p("""Step by step: at compile time, `broken` contains `count = 0`, so `count` is a local of `broken` everywhere in it.
    At run time, the first line reads that local before anything was assigned to it, which is `UnboundLocalError`. It does
    not fall back to the global `count`, because the decision "local or not" was made for the whole function before it ran.
    The same happens with `total += x` inside a function when `total` was meant to be the module's variable: `+=` is an
    assignment, so it makes `total` local."""),
    p("""The rule gives you three ways out, from best to worst: pass the value in as a parameter and return the new value;
    use a different local name; or declare that you mean the outer variable, with `global` or `nonlocal` (next section)."""),
)

section("global", "`global` and `nonlocal`",
    p("""`global name` at the top of a function says: in this function, `name` refers to the **module-level** variable,
    for reading and assigning. `nonlocal name` says the same about the nearest **enclosing function's** variable. Both are
    only needed to **rebind** the outer name. Changing a mutable object that an outer name already points at needs no
    declaration at all, because that is not an assignment to the name (2.2)."""),
    ex("""
    calls = 0
    seen = []

    def track(item):
        global calls
        calls += 1              # rebinds the global name: needs `global`
        seen.append(item)       # changes the global list in place: no declaration needed

    track("a"); track("b")
    print(calls, seen)

    def make_counter():
        n = 0
        def bump():
            nonlocal n          # rebinds outer's n, not a new local
            n += 1
            return n
        return bump

    bump = make_counter()
    print(bump(), bump(), bump())
    """, "global_nonlocal.py"),
    p("""`nonlocal` is what makes a closure that keeps changing state, like this counter, work (lesson 3.4 is about
    closures). `global` is legal but usually a sign of hidden shared state, which is the next section's subject."""),
)

section("state", "Why module-level state hurts",
    p("""A function that reads or writes a global variable depends on something its signature does not show. In data and
    LLM code that causes three specific problems:"""),
    p("""- **Results depend on history.** A global counter, cache or "current model" means calling the same function
      twice can give different results, which breaks reproducibility and notebooks run out of order.
    - **Tests interfere with each other.** One test changes the global, and the next test sees the changed value.
    - **Concurrency breaks it.** In a web server (FastAPI) or with threads, many requests share one module, so a global
      "current user" or "last prompt" leaks between requests (Module 14)."""),
    ex("""
    current_user = None                       # module state: shared by every request

    def handle(user, question):
        global current_user
        current_user = user
        return answer(question)

    def answer(question):
        return f"answering {question!r} for {current_user}"

    print(handle("ana", "refund?"))
    # Imagine two requests interleaved in a server: the second overwrites current_user
    current_user = "ben"
    print(answer("refund?"))                  # a later call sees whoever wrote last
    """, "module_state.py"),
    p("""The fix is almost always the same: pass what a function needs as **parameters**, return results, and keep state
    in an object that is created per run or per request (a dict, a class instance in Module 9, or FastAPI's request-scoped
    dependencies). Module-level **constants** (`MAX_TOKENS = 4096`, a compiled regex, a loaded config that is never
    changed) are fine; module-level **variables that change** are the problem."""),
)

section("shadowing", "Shadowing built-ins, and two special scopes",
    p("""Because built-ins are searched **last**, any global or local with the same name hides them. Naming a variable
    `list`, `id`, `sum`, `max`, `input`, `type` or `dict` is legal, and breaks every later use of the built-in in that
    scope with a confusing error far from the cause."""),
    ex("""
    def total_length(docs):
        sum = 0                     # shadows the built-in sum inside this function
        for d in docs:
            sum += len(d)
        return sum

    print(total_length(["ab", "cde"]))

    def average_length(docs):
        sum = 0
        for d in docs:
            sum += len(d)
        return sum / len(docs), sum([1, 2])   # the built-in is gone here

    try:
        average_length(["ab"])
    except TypeError as e:
        print("TypeError:", e)
    """, "shadowing.py"),
    p("""Two places have scope rules worth knowing. A **comprehension** has its own scope, so its loop variable does not leak
    out (unlike a `for` loop). And a **class body** is a scope that is **not** an enclosing scope for the methods inside it:
    a method cannot see a class-level name without `self.` or the class name (Module 9)."""),
    ex("""
    x = "outer"
    squares = [x * 2 for x in range(3)]
    print(squares, x)              # the comprehension's x did not leak

    for y in range(3):
        pass
    print(y)                       # a for loop's variable does leak
    """, "comprehension_scope.py"),
)

section("warmup", "Warm-up",
    predict("Which scope wins?", "easy",
        code="""
        name = "global"

        def outer():
            name = "enclosing"
            def inner():
                return name
            def own():
                name = "local"
                return name
            return inner(), own(), name

        print(outer())
        print(name)
        """,
        hints=["Each function's assignments make names local to that function only."],
        why="""`inner` assigns nothing, so it reads `name` from the enclosing `outer`. `own` assigns `name`, so it has its own
        local. `outer` returns its own variable. None of them touch the module's `name`, which is still `"global"`: an
        assignment inside a function never changes an outer name unless you declare `global` or `nonlocal`."""),
    fix("A running total that crashes", "easy",
        prompt="""`add_tokens` should keep a running total of tokens used across calls, stored in the module. It raises
        `UnboundLocalError`. Fix it **without** `global`: make the function take the current total and return the new one.""",
        code="""
        total_tokens = 0

        def add_tokens(n):
            total_tokens += n
            return total_tokens
        """,
        tests="""
        t = 0
        t = add_tokens(t, 120)
        t = add_tokens(t, 80)
        assert t == 200
        assert add_tokens(0, 5) == 5
        """,
        hints=["`total_tokens += n` is an assignment, so `total_tokens` is local to the whole function.",
               "Change the signature to `add_tokens(total, n)` and return `total + n`."],
        solution="""
        def add_tokens(total, n):
            return total + n
        """,
        why="""`+=` is an assignment, so the compiler makes `total_tokens` local, and the read on the same line finds an
        unassigned local. `global total_tokens` would silence the error but keep hidden shared state. Passing the total in and
        returning the new one makes the function pure (2.4): its result depends only on its arguments, so it is trivial to
        test, and two separate runs (or two users) can keep separate totals."""),
    predict("Comprehension and loop variables", "easy",
        code="""
        i = "start"
        doubled = [i * 2 for i in range(3)]
        print(doubled, i)

        for i in range(3):
            pass
        print(i)

        labels = {k: len(k) for k in ["ab", "c"]}
        try:
            print(k)
        except NameError as e:
            print("NameError:", e)
        """,
        hints=["Comprehensions have their own scope. A `for` loop does not."],
        why="""The list comprehension's `i` lives in the comprehension's own scope, so the outer `i` stays `"start"`. The plain
        `for` loop assigns the module's `i`, which keeps its last value, 2. The dict comprehension's `k` never existed outside
        it, so reading `k` afterwards is a `NameError`."""),
    predict("Changing versus rebinding a global", "easy",
        code="""
        cache = {}
        hits = 0

        def remember(key, value):
            cache[key] = value

        def reset_cache():
            cache = {}

        def count_hit():
            global hits
            hits += 1

        remember("a", 1)
        reset_cache()
        count_hit(); count_hit()
        print(cache, hits)
        """,
        hints=["Which of these functions assign to a name, and which only change an object?"],
        why="""`remember` changes the global dict in place, so no declaration is needed and the change is visible. `reset_cache`
        **assigns** `cache = {}`, which makes `cache` local to that function: the global dict is not reset at all, a bug that
        raises no error. `count_hit` declares `global hits`, so its `+=` rebinds the module's name. To empty the global dict
        without `global`, call `cache.clear()`."""),
)

section("medium", "Medium",
    fix("A request handler that leaks users", "medium", tag="GenAI",
        prompt="""This tiny chat backend stores the current user in a global, which leaks between interleaved requests.
        Remove the module-level state: `handle` should pass the user to `answer` explicitly, and nothing outside the
        functions should change.""",
        code="""
        current_user = None

        def answer(question):
            return f"{current_user}: {question}"

        def handle(user, question):
            global current_user
            current_user = user
            return answer(question)
        """,
        tests="""
        assert handle("ana", "refund?") == "ana: refund?"
        assert handle("ben", "invoice?") == "ben: invoice?"
        assert answer("x", user="cy") == "cy: x"
        assert "current_user" not in globals()
        """,
        hints=["Give `answer` a `user` parameter and have `handle` pass it."],
        solution="""
        def answer(question, user):
            return f"{user}: {question}"

        def handle(user, question):
            return answer(question, user=user)
        """,
        why="""In a real server, requests run interleaved (async) or in parallel (threads), so between `current_user = user`
        and the use in `answer`, another request can overwrite the global. That is a data leak between users, and it never
        shows up in single-user testing. Passing the user explicitly makes every function's inputs visible in its signature.
        Frameworks give you per-request values the safe way: FastAPI dependencies, or `contextvars` for values that must flow
        through many layers (Module 14)."""),
    trace("Names in three scopes", "medium",
        prompt="Fill in the module-level `x` and `log` after each marked line.",
        code="""
        x = 1
        log = []

        def f():
            x = 2
            log.append(x)

        def g():
            global x
            x = 3
            log.append(x)

        def h():
            log = ["local"]
            log.append(x)

        f()  # row: "f()"
        g()  # row: "g()"
        h()  # row: "h()"
        """,
        trace_vars=["x", "log"],
        hints=["Only `g` declares `global`. `h` assigns `log`, so its `log` is a different, local list."],
        why="""`f` assigns a local `x`, so the global stays 1, but `log.append` changes the global list. `g` rebinds the global
        `x` to 3 and appends 3. `h` creates its own local `log`, so its append (of the global `x`, 3) goes into a list that is
        thrown away when `h` returns: the global `log` is unchanged. Three functions, three different scope outcomes, and
        none of them raised an error."""),
    write("A call counter without globals", "medium", tag="GenAI",
        prompt="""You want to count how many times an LLM client function is called, per client. Write `make_counted(fn)`
        that returns `(wrapper, get_count)`: `wrapper(*args, **kwargs)` calls `fn` and counts the call, and `get_count()`
        returns the number of calls so far. Each `make_counted` call must have its own independent count. Use `nonlocal`,
        not a global.""",
        code="""
        def make_counted(fn):
            pass
        """,
        tests="""
        def complete(prompt, *, model="small"):
            return f"{model}:{prompt}"
        w1, c1 = make_counted(complete)
        w2, c2 = make_counted(complete)
        assert w1("a") == "small:a" and w1("b", model="large") == "large:b"
        w2("x")
        assert c1() == 2 and c2() == 1
        """,
        hints=["Keep `count = 0` inside `make_counted`, define `wrapper` and `get_count` inside it, and use `nonlocal count` in `wrapper`."],
        solution="""
        def make_counted(fn):
            count = 0

            def wrapper(*args, **kwargs):
                nonlocal count
                count += 1
                return fn(*args, **kwargs)

            def get_count():
                return count

            return wrapper, get_count
        """,
        why="""`count` lives in the scope of one `make_counted` call, so every call creates a separate counter, unlike a module
        global that all clients would share. `wrapper` needs `nonlocal` because `count += 1` rebinds the name; `get_count` only
        reads it, so it needs nothing. Both inner functions see the **same** `count`, which is why the getter reports what the
        wrapper counted. This is a closure (lesson 3.4) and the core of a decorator (Module 7)."""),
    fix("A variable named after a built-in", "medium", tag="Data work",
        prompt="""This summarises scores, but crashes on the line that uses `max`. Find the cause and fix it without
        changing what the function returns.""",
        code="""
        def summarise(scores):
            max = 1.0                         # the best possible score
            total = sum(scores)
            best = max(scores)
            return {"mean": total / len(scores), "best": best, "best_possible": max}
        """,
        tests="""
        assert summarise([0.2, 0.8, 0.5]) == {"mean": 0.5, "best": 0.8, "best_possible": 1.0}
        assert summarise([1.0]) == {"mean": 1.0, "best": 1.0, "best_possible": 1.0}
        """,
        hints=["What does the name `max` refer to on the line `best = max(scores)`?"],
        solution="""
        def summarise(scores):
            best_possible = 1.0
            total = sum(scores)
            best = max(scores)
            return {"mean": total / len(scores), "best": best, "best_possible": best_possible}
        """,
        why="""`max = 1.0` makes `max` a local float for the whole function, so `max(scores)` tries to call a float: `TypeError:
        'float' object is not callable`. The error points at the call, not at the assignment that caused it, which is what
        makes shadowing confusing. Linters flag it (Ruff rule A001, from flake8-builtins). Common victims in data code are
        `id`, `type`, `filter`, `input`, `max`, `min`, `sum`, `list` and `dict`."""),
    choose("Looking up a setting inside the loop", "medium",
        prompt="Both scale a million numbers by a factor stored deep inside a module-level config. Which loop is faster?",
        setup="""CONFIG = {"model": {"scaling": {"factor": 3}}}
xs = list(range(1_000_000))
def scale_lookup(xs):
    out = []
    for x in xs:
        out.append(x * CONFIG["model"]["scaling"]["factor"])
    return out
def scale_once(xs):
    factor = CONFIG["model"]["scaling"]["factor"]
    out = []
    for x in xs:
        out.append(x * factor)
    return out""",
        options={
            "a": "r = scale_lookup(xs)",
            "b": "r = scale_once(xs)",
        },
        answer="b",
        hints=["How many lookups does each pass of A perform before it can multiply?"],
        why="""A reads the global `CONFIG` and then does three dict lookups on **every** pass, a million times, to fetch a value
        that never changes. B does them once, before the loop, and keeps the result in a local name, which is the cheapest
        kind of name to read (locals live in fixed slots of the function's frame). Recent Pythons have made plain global reads
        almost as fast as local ones, so the win here comes mainly from the repeated dict lookups. The habit is worth having
        in hot loops over big data: hoist anything that does not change out of the loop. A list comprehension or numpy would
        be faster again."""),
    fix("Settings you can only change through a global", "medium", tag="ML",
        prompt="""These helpers all read a module-level `CONFIG`, so an experiment with a stricter threshold has to change
        the global, which leaks into everything else. Change them so each takes the config as a parameter (defaulting to
        `CONFIG`), with the same behaviour for existing callers.""",
        code="""
        CONFIG = {"threshold": 0.5, "positive": "spam", "negative": "ham"}

        def classify(score):
            if score >= CONFIG["threshold"]:
                return CONFIG["positive"]
            return CONFIG["negative"]

        def classify_all(scores):
            return [classify(s) for s in scores]
        """,
        tests="""
        assert classify_all([0.9, 0.1, 0.5]) == ["spam", "ham", "spam"]
        assert classify(0.49) == "ham"
        strict = {"threshold": 0.8, "positive": "spam", "negative": "ham"}
        assert classify_all([0.7, 0.9], config=strict) == ["ham", "spam"]
        assert CONFIG["threshold"] == 0.5
        """,
        hints=["Give both functions a `config` parameter, defaulting to `CONFIG`, and pass it down from `classify_all` to `classify`."],
        solution="""
        CONFIG = {"threshold": 0.5, "positive": "spam", "negative": "ham"}

        def classify(score, config=CONFIG):
            return config["positive"] if score >= config["threshold"] else config["negative"]

        def classify_all(scores, config=CONFIG):
            return [classify(s, config) for s in scores]
        """,
        why="""Each function now shows its dependency in its signature, and a test or an experiment can pass a different config
        without touching the global. Using `CONFIG` as a default is fine here because these functions never change it; the
        mutable-default warning from 2.4 is about defaults that get changed. If you want to be sure nobody changes it, freeze
        it (2.3, `MappingProxyType`). Adding a parameter **with a default** keeps every existing caller working, which is
        why the first two tests pass with both versions."""),
)

section("hard", "Hard",
    predict("UnboundLocalError in disguise", "hard",
        code="""
        import json

        def parse_all(lines):
            out = []
            for line in lines:
                out.append(json.loads(line))
            if not out:
                import json
            return out

        try:
            print(parse_all(['{"a": 1}']))
        except UnboundLocalError as e:
            print("UnboundLocalError:", e)

        total = 0
        def add(values):
            for v in values:
                total = total + v
            return total
        try:
            add([1, 2])
        except UnboundLocalError as e:
            print("UnboundLocalError:", e)
        """,
        hints=["`import` is an assignment. So is a `for` loop's target and a plain `=`.",
               "The `import json` is never even executed. Does that matter at compile time?"],
        why="""The `import json` inside the `if` assigns the name `json`, so the compiler makes `json` local to the **whole**
        function, including the loop above it, even though that line never runs. `json.loads` then reads an unassigned local.
        In `add`, `total = total + v` assigns `total`, so the right-hand side reads the unassigned local `total`. Both show that
        "local or global" is decided when the function is compiled, from every assignment anywhere in it, not by which lines
        happen to run."""),
    fix("Read the code: a pipeline with hidden state", "hard", tag="ML",
        prompt="""This preprocessing module keeps its vocabulary and statistics in module-level variables. Fitting on a
        second dataset mixes in the first one's vocabulary, and transforming before fitting silently uses stale values.
        Rewrite it so `fit` **returns** the fitted state and `transform` takes that state as a parameter. No module-level
        variable may change.""",
        code="""
        VOCAB = {}
        MEAN_LEN = 0.0


        def fit(texts):
            global MEAN_LEN
            for text in texts:
                for word in text.lower().split():
                    if word not in VOCAB:
                        VOCAB[word] = len(VOCAB)
            MEAN_LEN = sum(len(t.split()) for t in texts) / len(texts)


        def transform(text):
            ids = [VOCAB.get(w, -1) for w in text.lower().split()]
            return {"ids": ids, "len_ratio": len(ids) / MEAN_LEN}
        """,
        tests="""
        state_a = fit(["the cat sat", "the dog"])
        state_b = fit(["a bird"])
        assert state_a["vocab"] == {"the": 0, "cat": 1, "sat": 2, "dog": 3}
        assert state_b["vocab"] == {"a": 0, "bird": 1}
        assert transform("The bird", state_b) == {"ids": [-1, 1], "len_ratio": 1.0}
        assert transform("the cat", state_a) == {"ids": [0, 1], "len_ratio": 0.8}
        """,
        hints=["Build the vocabulary and the mean in local variables inside `fit`, and return them in a dict.",
               "`transform(text, state)` reads `state[\"vocab\"]` and `state[\"mean_len\"]`."],
        solution="""
        def fit(texts):
            vocab = {}
            for text in texts:
                for word in text.lower().split():
                    if word not in vocab:
                        vocab[word] = len(vocab)
            mean_len = sum(len(t.split()) for t in texts) / len(texts)
            return {"vocab": vocab, "mean_len": mean_len}


        def transform(text, state):
            ids = [state["vocab"].get(w, -1) for w in text.lower().split()]
            return {"ids": ids, "len_ratio": len(ids) / state["mean_len"]}
        """,
        why="""The original has both scope bugs from this lesson. `VOCAB` is changed in place without `global`, so every `fit`
        call adds to the same dict and the second dataset's ids continue after the first's. `MEAN_LEN` is rebound with
        `global`, so `transform` reads whichever fit ran last, or 0.0 before any fit (a `ZeroDivisionError` far from the cause).
        Returning the state makes "fitted" a value you can store, pass, compare and version. That is exactly the
        `fit`/`transform` design of scikit-learn, except that it keeps the state on the estimator object (`vocabulary_`,
        `mean_`), one object per fit, never at module level."""),
    predict("Late lookup of globals", "hard",
        code="""
        def make_prompt(question):
            return f"[{STYLE}] {question}"

        STYLE = "brief"
        print(make_prompt("refunds?"))
        STYLE = "formal"
        print(make_prompt("refunds?"))

        def reader():
            return LIMIT * 2
        try:
            reader()
        except NameError as e:
            print("NameError:", e)
        LIMIT = 21
        print(reader())
        """,
        hints=["A function looks up a global name when the line runs, not when the function is defined."],
        why="""`make_prompt` was defined before `STYLE` existed, which is fine: globals are looked up **each time the line
        runs**, so the function always sees the current value. The same rule makes `reader()` fail before `LIMIT` exists and
        work afterwards. Handy for constants, dangerous for anything that changes: a function's behaviour can change because
        some other code reassigned a module variable."""),
    write("Count words without leaking state", "hard", tag="Data work",
        prompt="""Write `make_word_counter()` that returns three functions `(add, top, reset)` sharing one private word
        count: `add(text)` counts the lower-cased words of `text`, `top(n)` returns the `n` most common `(word, count)` pairs
        (highest count first, ties in first-seen order), and `reset()` clears the counts. Two counters must never share data,
        and nothing at module level may change.""",
        code="""
        def make_word_counter():
            pass
        """,
        tests="""
        add, top, reset = make_word_counter()
        add2, top2, _ = make_word_counter()
        add("The cat and the hat")
        add("the end")
        add2("other")
        assert top(2) == [("the", 3), ("cat", 1)]
        assert top2(5) == [("other", 1)]
        reset()
        assert top(3) == []
        add("again again")
        assert top(1) == [("again", 2)]
        """,
        hints=["Keep `counts = {}` in the outer function. `add` and `reset` change that dict in place, so do they need `nonlocal`?",
               "`sorted(counts.items(), key=lambda kv: -kv[1])` sorts by count, and Python's sort is stable, so ties keep insertion order."],
        solution="""
        def make_word_counter():
            counts = {}

            def add(text):
                for word in text.lower().split():
                    counts[word] = counts.get(word, 0) + 1

            def top(n):
                return sorted(counts.items(), key=lambda kv: -kv[1])[:n]

            def reset():
                counts.clear()

            return add, top, reset
        """,
        why="""All three functions close over the same `counts` dict, and every operation changes that dict **in place**
        (`counts[word] = ...`, `counts.clear()`), so no `nonlocal` is needed. If `reset` were written `counts = {}` it would
        create a new local dict and the shared counts would not be cleared, the same bug as `reset_cache` in problem 4, and
        `nonlocal counts` would be required. Sorting with a negated count keeps ties in insertion order because Python's sort
        is stable (lesson 4.2). `collections.Counter` does the counting part for you (lesson 4.6)."""),
)

section("interview", "Interview questions",
    explain("Explain the LEGB rule, and why assigning to a variable inside a function can cause UnboundLocalError.", "medium", tag="Interview",
        why="""When Python reads a name it searches Local, Enclosing, Global, then Built-in scopes and uses the first match.
        Which scope a name belongs to in a function is decided at **compile time**: if the name is assigned anywhere in the
        function (`=`, `+=`, `for`, `import`, `def`, `with ... as`), it is local throughout that function. So reading it
        before the assignment raises `UnboundLocalError` instead of falling back to the global. Fixes: pass the value in and
        return the result, use a different name, or declare `global` / `nonlocal` if you really mean the outer variable.
        Mention that only rebinding needs a declaration; changing a mutable outer object in place does not."""),
    explain("What is the difference between `global` and `nonlocal`, and when should you use them?", "medium", tag="Interview",
        why="""`global x` makes `x` refer to the module-level variable for reading and rebinding inside the function.
        `nonlocal x` makes it refer to the nearest enclosing function's variable, and is an error if no enclosing function has
        one. `nonlocal` is the normal tool for closures that update state (counters, accumulators, memoising wrappers).
        `global` is legal but usually a design smell: hidden shared state makes code non-reproducible, hard to test and unsafe
        under concurrency. Prefer parameters and return values, or an object that owns the state."""),
    explain("Your FastAPI app stores the current user's id in a module variable. What can go wrong, and what do you do instead?", "hard", tag="Interview",
        why="""A module is loaded once per worker process and shared by every request that process handles. With async
        endpoints, requests interleave at every `await`; with threads, they run at the same time. So one request can set the
        variable and another can overwrite it before the first one reads it, and responses (or LLM context) for one user get
        built with another user's data. It never shows in single-user testing. Instead: pass the user explicitly, use FastAPI
        dependencies (`Depends`) that compute per-request values, or `contextvars.ContextVar` when a value must flow through
        many layers, since it gives each request (task) its own value. Module-level constants and read-only clients are fine;
        module-level mutable per-request data is not."""),
)

recap(
    "Reading a name searches Local, Enclosing, Global, Built-in. Only functions (and comprehensions, classes) create scopes, not `if` or `for`.",
    "Any assignment anywhere in a function makes that name local for the whole function, decided at compile time. That is the source of `UnboundLocalError`.",
    "`global` / `nonlocal` are needed only to rebind an outer name; changing an outer mutable object in place needs no declaration.",
    "Module-level variables that change make results depend on history, tests interfere, and servers leak data between requests. Pass values in and return results.",
    "Never name variables after built-ins (`list`, `id`, `max`, `sum`): the error appears far from the cause.",
)
