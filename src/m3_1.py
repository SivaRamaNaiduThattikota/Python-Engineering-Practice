from lesson import *

lesson(
    id="m3-1", num="3.1", title="Defining and calling functions",
    intro="What `def` really does, how Python matches arguments to parameters and what its error messages mean, "
          "the missing-return bug, and the function metadata that frameworks like FastAPI read to call your code.",
    desc="Parameters, return values, `None`, defaults and docstrings.",
    keys="def function object call parameter argument positional keyword return none implicit early return guard clause docstring annotations signature inspect recursion base case recursion limit typeerror",
)

term("Function object", "What `def` creates: an object holding the code, the defaults and metadata such as `__name__` and `__doc__`, bound to the function's name.")
term("Guard clause", "An early `return` or `raise` at the top of a function that deals with a special case, so the main logic is not nested.")
term("Signature", "The parameters of a function with their kinds and defaults. `inspect.signature(f)` returns it as an object.")
term("Recursion", "A function that calls itself on a smaller part of the problem, with a base case that stops it.")

section("def", "What `def` does, step by step",
    p("""`def` is not a declaration that exists before the program starts. It is a **statement that runs**, at the moment
    Python reaches it, like an assignment. Running it does four things, in this order:"""),
    p("""- **1. Evaluate the defaults.** Every default value in the signature is computed now, once (this is the 2.4
      rule about mutable defaults).
    - **2. Build a function object.** It holds the compiled body (`__code__`), the defaults (`__defaults__`), the
      docstring (`__doc__`), the name (`__name__`) and a link to the module's global names.
    - **3. Bind the name.** The function's name is pointed at that object, exactly like `name = object` (2.1).
    - **4. Do not run the body.** The body runs only when the function is **called**, and it runs again from the top
      on every call."""),
    ex("""
    def greet(name):
        return f"Hi, {name}"

    print(type(greet).__name__, greet.__name__)
    print(greet)                     # the object itself; nothing has run yet
    print(greet("Ana"))              # calling it runs the body
    """, "def_object.py"),
    p("""Step 4 surprises people: an error inside the body is not found when `def` runs, only when the faulty line is
    actually reached during a call. A function can sit in a module for months with a typo in a branch that is rarely
    taken."""),
    ex("""
    def risky(flag):
        if flag:
            return undefined_name + 1   # a NameError waiting to happen
        return "fine"

    print("def ran without any error")
    print(risky(False))
    try:
        risky(True)
    except NameError as e:
        print("NameError:", e)
    """, "body_runs_later.py"),
    p("""Because `def` is an assignment in disguise, everything from Module 2 applies to function names too. Running
    `def` again builds a **new** function object and moves the name; anything still holding the old object keeps the
    old code. A `def` inside a loop builds a new function on every pass. And a function cannot be called before its
    `def` has run."""),
    ex("""
    def greet():
        return "v1"

    old = greet                # another name for the same function object
    def greet():
        return "v2"            # a NEW function object; the name greet moves to it
    print(old(), greet(), old is greet)

    made = []
    for i in range(3):
        def step():
            return "step"
        made.append(step)
    print(len({id(f) for f in made}))   # three different function objects

    try:
        later()
    except NameError as e:
        print("NameError:", e)
    def later():
        return "too late"
    """, "def_rebinds.py"),
    callout("sql", "SQL / Power BI", """`def` is like `CREATE OR REPLACE PROCEDURE`: it runs when the script reaches it,
    and running it again replaces the definition. One difference matters: in Python, an old reference (here `old`) keeps
    calling the old version, while SQL always calls the current procedure by name. In notebooks this is how a stale
    version of a function keeps running inside a list, a dict or a callback that captured it before you edited it."""),
)

section("calls", "How a call fills the parameters",
    p("""When you call a function, Python builds the parameter values in a fixed order. Knowing the order lets you
    predict any call, and read any error message, without guessing:"""),
    p("""- **1. Positional arguments** fill the positional parameters from left to right. If there are more positional
      arguments than positional slots, the extras go into `*args` if the function has it, otherwise it is an error.
    - **2. Keyword arguments** fill parameters by name. A name that was already filled in step 1 is an error
      ("multiple values"); a name that matches no parameter goes into `**kwargs` if there is one, otherwise it is an
      error ("unexpected keyword").
    - **3. Defaults** fill any parameter that is still empty.
    - **4. Anything still empty** is an error ("missing required argument")."""),
    p("""Here is that algorithm worked through for one call to `embed(texts, model="small", *, batch_size=32)`. The `*`
    makes `batch_size` keyword-only: after the `*`, no positional argument can reach it (lesson 3.2 covers `*`, `/`,
    `*args` and `**kwargs` in depth)."""),
    html("""<div class="tbl"><table>
      <tr><th>Call: <code>embed(["a", "b"], batch_size=8)</code></th><th><code>texts</code></th><th><code>model</code></th><th><code>batch_size</code></th></tr>
      <tr><td>1. positional, left to right</td><td><code>["a", "b"]</code></td><td>(empty)</td><td>(not reachable by position)</td></tr>
      <tr><td>2. keywords, by name</td><td><code>["a", "b"]</code></td><td>(empty)</td><td><code>8</code></td></tr>
      <tr><td>3. defaults</td><td><code>["a", "b"]</code></td><td><code>"small"</code></td><td><code>8</code></td></tr>
      <tr><td>4. anything missing?</td><td colspan="3">no, so the body runs</td></tr>
    </table></div>"""),
    ex("""
    def embed(texts, model="small", *, batch_size=32):
        return f"{len(texts)} texts, {model}, batch {batch_size}"

    print(embed(["a", "b"]))
    print(embed(["a"], "large", batch_size=8))
    print(embed(batch_size=4, texts=["x"]))      # keywords can come in any order

    for bad in ['embed()', 'embed(["a"], "large", 64)', 'embed(["a"], texts=["b"])', 'embed(["a"], mdl="x")']:
        try:
            eval(bad)
        except TypeError as e:
            print(f"{bad:28} -> {e}")
    """, "matching.py"),
    p("""Each error message names the function and the exact parameter, and each one is a failed step of the algorithm:
    **missing** (step 4), **takes from 1 to 2 positional arguments but 3 were given** (step 1: `batch_size`
    cannot be filled by position), **multiple values** (step 2: `texts` was already filled by position) and **unexpected keyword**
    (step 2: a typo). When an LLM tool call or a framework call fails, one of these four messages is usually the whole
    story, so it pays to read them word by word instead of skimming."""),
    p("""One rule is enforced even before the call runs: in the call itself, positional arguments must come before keyword
    arguments. `embed(model="large", ["a"])` is a `SyntaxError`, found when the code is compiled, not when it runs."""),
)

section("returns", "What `return` does",
    p("""`return expression` does three things: it evaluates the expression, **ends the function immediately** (no line
    after it in that call runs), and hands the resulting **object** back to the caller. Nothing is copied: the caller
    receives the very object the function built or was given (2.4). If the function reaches the end of its body without
    a `return`, or runs a bare `return`, the result is `None`."""),
    ex("""
    def first_long_word(words, n):
        for w in words:
            if len(w) > n:
                return w            # ends the whole function, not just the loop
        return None                 # explicit: nothing matched

    print(first_long_word(["rag", "retrieval", "embedding"], 5))
    print(first_long_word(["rag"], 5))

    def no_return():
        x = 1 + 1                   # computed, then thrown away

    print(no_return())
    """, "return_ends.py"),
    p("""A function returns exactly **one object**. `return a, b` builds one tuple, and the caller can unpack it into
    names. That is convenient for two or three values, and it is also where the most common return bug shows up: a
    branch that forgets to return, so some inputs silently get `None`."""),
    ex("""
    def label(score):
        if score > 0.6:
            return "positive"
        elif score < 0.4:
            return "negative"
        # no return here: scores from 0.4 to 0.6 fall off the end

    print(label(0.9), label(0.1), label(0.5))

    def bounds(xs):
        return min(xs), max(xs)     # one tuple
    lo, hi = bounds([4, 1, 9])
    print(bounds([4, 1, 9]), lo, hi)
    """, "missing_return.py"),
    p("""Two habits prevent the missing-return bug. Make every path end in an explicit `return`, writing the last case as
    the plain fall-through (`return "neutral"`) rather than another `elif`. And use **guard clauses**: handle the special
    cases first with an early `return` or `raise`, so the main logic is not buried in nested `if`s."""),
    ex("""
    def safe_ratio(hits, total):
        if total < 0 or hits < 0:
            raise ValueError("counts must be non-negative")
        if total == 0:
            return 0.0              # guard clause: special case handled first
        return hits / total         # the main case, not nested

    print(safe_ratio(3, 4), safe_ratio(0, 0))
    """, "guard_clauses.py"),
    callout("warn", "`print` is not `return`", """In a notebook, a function that **prints** its result looks exactly like one
    that **returns** it, because both show the value under the cell. But only a returned value can be stored, compared,
    tested or passed on. `total = report(rows)` gives `None` if `report` only printed. Library functions return; printing
    is for the outermost layer that talks to a person."""),
    callout("note", "Choosing what to return", """Return a tuple for two or three closely related values
    (`lo, hi = bounds(xs)`). Beyond that, callers have to remember positions, so return a dict or, better, a dataclass or
    `NamedTuple` with named fields (Module 11). And return the same **kind** of thing from every path: a function that
    returns a list in one branch and `None` in another forces every caller to check (problem 8)."""),
)

section("metadata", "Docstrings, type hints and signatures",
    p("""The first string in a function body is its **docstring**: Python stores it as `__doc__`, and `help(f)` and every
    editor show it. Type hints (`query: str`, `-> list`) are stored in `__annotations__`. Python itself **does not check
    them** at run time; they are information for people, editors, type checkers (Module 11) and frameworks."""),
    ex("""
    def double(x: int) -> int:
        "Return twice x."
        return x * 2

    print(double.__doc__, double.__annotations__)
    print(double(21), double("ab"))    # the hint says int, but nothing stops a str
    """, "hints_not_enforced.py"),
    p("""`inspect.signature(f)` turns a function's parameters into objects you can examine: each parameter's name, its
    **kind** (positional, keyword-only and so on), its default and its annotation."""),
    ex("""
    import inspect

    def search(query: str, k: int = 5, *, rerank: bool = False):
        "Search the index and return the top k chunks."
        return []

    sig = inspect.signature(search)
    print(sig)
    for name, param in sig.parameters.items():
        print(f"{name:7} {param.kind.name:22} default={param.default!r:8} type={param.annotation.__name__}")
    """, "signature.py"),
    p("""This is exactly how **FastAPI** works out that `k` is an optional query parameter with default 5 that must be
    an int: it reads the signature of your endpoint function when you register it. Agent frameworks do the same to turn
    a Python function into a tool description for an LLM, using the docstring as the tool's description. Because
    functions are objects that describe themselves, a framework can call your code correctly without you writing any
    glue (problem 15)."""),
)

section("recursion", "Recursion, step by step",
    p("""A function can call itself. **Recursion** fits data that is nested to an unknown depth, such as JSON from an API
    or a document tree: handle one level, call the same function on each child, and stop at a **base case** that needs
    no further call. You already wrote two recursive functions in 2.3 (`freeze` and `with_override`)."""),
    p("""What happens on each call: Python creates a new **frame** (a private set of local variables) for that call and
    puts it on top of the **call stack**. The caller's frame waits underneath, paused at the call. When the inner call
    returns, its frame is removed and the caller continues with the result. Printing the depth makes the stack visible:"""),
    ex("""
    def depth(obj, level=0):
        pad = "  " * level
        if isinstance(obj, dict):
            print(f"{pad}dict with {len(obj)} keys")
            result = 1 + max((depth(v, level + 1) for v in obj.values()), default=0)
        elif isinstance(obj, list):
            print(f"{pad}list with {len(obj)} items")
            result = 1 + max((depth(v, level + 1) for v in obj), default=0)
        else:
            print(f"{pad}value {obj!r}")
            result = 0              # base case: a plain value needs no further call
        return result

    print("depth =", depth({"a": {"b": [1, 2]}, "c": 3}))
    """, "recursion_trace.py"),
    p("""Each indented line is one frame deeper on the stack. The plain values are the base cases; every dict or list waits
    for its children and then adds 1. The `default=0` matters: an empty dict or list has no children, and `max` of nothing
    would otherwise raise (problem 6)."""),
    p("""Two limits come with recursion in Python. Each frame costs memory and time, and CPython caps the depth (1,000
    frames by default; `sys.getrecursionlimit()` shows the value). Python also does not optimise tail calls, so even a
    recursion whose last action is the recursive call still uses one frame per level. A missing or unreachable base case
    therefore ends in a `RecursionError` rather than running forever:"""),
    ex("""
    def countdown(n):
        if n == 0:                  # base case, but a negative start never reaches it
            return "done"
        return countdown(n - 1)

    print(countdown(5))
    try:
        countdown(-1)
    except RecursionError as e:
        print("RecursionError:", e)
    """, "recursion_limit.py"),
    p("""For very deep data, or for simple repetition, write a loop. A tree can be walked without recursion by keeping your
    own stack in a list, which has no depth limit:"""),
    ex("""
    def max_depth(obj):
        best = 0
        stack = [(obj, 0)]          # (value, depth so far): our own call stack
        while stack:
            value, d = stack.pop()
            if isinstance(value, dict):
                children = value.values()
            elif isinstance(value, list):
                children = value
            else:
                best = max(best, d)
                continue
            if not children:
                best = max(best, d + 1)
            for child in children:
                stack.append((child, d + 1))
        return best

    print(max_depth({"a": {"b": [1, 2]}, "c": 3}), max_depth([]), max_depth(42))
    """, "explicit_stack.py"),
    callout("sql", "SQL / Power BI", """A recursive Python function over a tree is the same idea as a SQL **recursive CTE**
    walking an org chart or a bill of materials: an anchor query (the base case) plus a recursive part that joins one level
    deeper, with a depth limit (`MAXRECURSION` in SQL Server) to stop runaway recursion."""),
)

section("warmup", "Warm-up",
    predict("Redefining a function", "easy",
        code="""
        def tokenizer():
            return "whitespace"

        current = tokenizer
        registry = {"default": tokenizer}

        def tokenizer():
            return "bpe"

        print(current(), registry["default"](), tokenizer())
        print(current is registry["default"], tokenizer.__name__)
        """,
        hints=["The second `def` builds a new function object and moves only the name `tokenizer`."],
        why="""`current` and the registry both hold the **first** function object, so they still return
        `"whitespace"`. Only the name `tokenizer` moved to the new one. Both objects are named `"tokenizer"`, because
        `__name__` is set from the `def`. This is why reloading code in a notebook can leave old versions running inside
        registries, callbacks and caches that captured the function earlier."""),
    fix("Scores in the middle get None", "easy", tag="ML",
        prompt="""`label_sentiment` maps a model's probability to a label. Scores from 0.4 to 0.6 should be
        `"neutral"`, but they come back as `None`. Fix it so every input gets a label.""",
        code="""
        def label_sentiment(p):
            if p > 0.6:
                return "positive"
            elif p < 0.4:
                return "negative"
            elif 0.4 <= p <= 0.6:
                "neutral"
        """,
        tests="""
        assert label_sentiment(0.9) == "positive"
        assert label_sentiment(0.1) == "negative"
        assert label_sentiment(0.5) == "neutral"
        assert label_sentiment(0.4) == "neutral" and label_sentiment(0.6) == "neutral"
        """,
        hints=["The last branch computes a string and throws it away. What is missing?",
               "Once `p > 0.6` and `p < 0.4` are ruled out, does the last case need a condition at all?"],
        solution="""
        def label_sentiment(p):
            if p > 0.6:
                return "positive"
            if p < 0.4:
                return "negative"
            return "neutral"
        """,
        why="""`"neutral"` on its own is an expression statement: it is computed and discarded, and the function falls off
        the end, returning `None`. Writing the last case as a plain `return "neutral"` both fixes the bug and removes a
        condition that could only drift out of sync with the others. A `None` label is a nasty ML bug, because it often
        survives until a metric silently counts it as a wrong class."""),
    predict("Reading call errors", "easy",
        code="""
        def rerank(query, docs, top_n=3, *, model="cross-encoder"):
            return len(docs[:top_n])

        calls = [
            'rerank("q", ["a", "b"])',
            'rerank("q", ["a", "b"], 1, "other")',
            'rerank("q", docs=["a"], query="q2")',
            'rerank("q")',
        ]
        for c in calls:
            try:
                print(eval(c))
            except TypeError as e:
                print("TypeError:", e)
        """,
        hints=["Count the positional arguments each call gives, and remember `model` can only be given by name."],
        why="""The first call works. The second passes four positional arguments, but only three parameters accept
        positions, because `model` is keyword-only. The third gives `query` twice: once by position and once by name.
        The fourth is missing the required `docs`. These exact messages are what you see when an LLM produces wrong
        arguments for a tool, so learning to read them pays off."""),
    write("Parse a score from LLM output", "easy", tag="GenAI",
        prompt="""An LLM was told to answer in the form `label: <word>, confidence: <number>`. Write
        `parse_label(text)` that returns a tuple `(label, confidence)` with the label lower-cased and the confidence as a
        float. Extra spaces anywhere must be tolerated.""",
        code="""
        def parse_label(text):
            pass
        """,
        tests="""
        assert parse_label("label: Positive, confidence: 0.82") == ("positive", 0.82)
        assert parse_label("  label:negative ,confidence:  0.3 ") == ("negative", 0.3)
        lab, conf = parse_label("label: neutral, confidence: 1")
        assert lab == "neutral" and conf == 1.0 and isinstance(conf, float)
        """,
        hints=["Split on the comma first, then split each part on the colon and `strip()` the pieces."],
        solution="""
        def parse_label(text):
            label_part, conf_part = text.split(",")
            label = label_part.split(":")[1].strip().lower()
            confidence = float(conf_part.split(":")[1].strip())
            return label, confidence
        """,
        why="""Returning a tuple lets callers unpack it in one line, `lab, conf = parse_label(...)`, which is the right
        size for two related values. Unpacking `label_part, conf_part = ...` also acts as a check: text with no comma, or
        two commas, raises `ValueError` instead of producing garbage. Real LLM output drifts from the requested format,
        which is why production code asks for JSON or uses structured-output features and validates the result (Module 11),
        but small parsers like this are everywhere."""),
)

section("medium", "Medium",
    write("Chunk text with overlap, and reject bad settings", "medium", tag="RAG",
        prompt="""Write `chunk_words(text, size, overlap=0)` that splits text into chunks of `size` words, where each chunk
        starts `size - overlap` words after the previous one, and the last chunk may be shorter. Use guard clauses: raise
        `ValueError` if `size < 1`, if `overlap < 0`, or if `overlap >= size`. Empty text gives `[]`.""",
        code="""
        def chunk_words(text, size, overlap=0):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        t = "a b c d e f g"
        assert chunk_words(t, 3) == ["a b c", "d e f", "g"]
        assert chunk_words(t, 3, 1) == ["a b c", "c d e", "e f g"]
        assert chunk_words("", 3) == []
        assert chunk_words("a b", 5) == ["a b"]
        assert raises(ValueError, chunk_words, t, 3, 3)
        assert raises(ValueError, chunk_words, t, 0)
        assert raises(ValueError, chunk_words, t, 3, -1)
        """,
        hints=["The start positions are `range(0, len(words), step)` with `step = size - overlap`.",
               "Stop once a chunk reaches the last word, or the overlap case produces a final chunk that is only overlap."],
        solution="""
        def chunk_words(text, size, overlap=0):
            if size < 1:
                raise ValueError("size must be at least 1")
            if overlap < 0 or overlap >= size:
                raise ValueError("overlap must be between 0 and size - 1")
            words = text.split()
            step = size - overlap
            chunks = []
            for start in range(0, len(words), step):
                chunks.append(" ".join(words[start:start + size]))
                if start + size >= len(words):
                    break
            return chunks
        """,
        why="""The guard clauses turn settings that would loop forever (`overlap == size` means a step of 0, and `range`
        rejects a step of 0 with its own unclear error) or make no sense into clear errors at the top, before any work. The
        `break` is the subtle part: without it, the overlap example would produce a fourth chunk `"g"` that is entirely
        overlap with the previous one, which wastes an embedding call and adds a duplicate result to retrieval. Real
        chunkers (for example in LangChain or LlamaIndex) count tokens rather than words, but follow the same structure."""),
    fix("The depth of an empty object", "medium", tag="Data work",
        prompt="""`depth` measures how deeply nested a JSON value is: plain values have depth 0, and each dict or list adds
        one. It crashes on empty dicts and lists. Fix it without special-casing every caller.""",
        code="""
        def depth(obj):
            if isinstance(obj, (dict, list)):
                children = obj.values() if isinstance(obj, dict) else obj
                return 1 + max(depth(c) for c in children)
            return 0
        """,
        tests="""
        assert depth(5) == 0
        assert depth({"a": 1}) == 1
        assert depth({"a": {"b": [1, 2]}}) == 3
        assert depth({}) == 1 and depth([]) == 1
        assert depth({"a": [], "b": {"c": {}}}) == 3
        """,
        hints=["What does `max()` do with an empty sequence? Check its `default` parameter."],
        solution="""
        def depth(obj):
            if isinstance(obj, (dict, list)):
                children = obj.values() if isinstance(obj, dict) else obj
                return 1 + max((depth(c) for c in children), default=0)
            return 0
        """,
        why="""`max()` of an empty iterable raises `ValueError: max() iterable argument is empty`, and a recursive function
        meets empty containers constantly, at every leaf of real JSON. `default=0` says "an empty container has no deeper
        children". Recursive functions need their base cases to cover **every** kind of leaf, and empty containers are the
        one people forget."""),
    refactor("One function, one job", "medium",
        prompt="""This function validates scores, computes statistics and formats a report, all in one block. Split it so
        each job is its own small function, with `report` calling them. Behaviour must stay the same. Keep the tests green.""",
        code="""
        def report(name, scores):
            if not scores:
                raise ValueError("no scores")
            for s in scores:
                if s < 0 or s > 1:
                    raise ValueError(f"bad score {s}")
            total = 0
            for s in scores:
                total += s
            mean = total / len(scores)
            best = scores[0]
            for s in scores:
                if s > best:
                    best = s
            return f"{name}: mean {mean:.2f}, best {best:.2f}, n={len(scores)}"
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert report("recall@5", [0.5, 0.75, 1.0]) == "recall@5: mean 0.75, best 1.00, n=3"
        assert raises(ValueError, report, "x", [])
        assert raises(ValueError, report, "x", [0.2, 1.5])
        """,
        hints=["Three jobs: `validate_scores(scores)`, `summarise(scores)` returning `(mean, best, n)`, and `report` that formats."],
        solution="""
        def validate_scores(scores):
            if not scores:
                raise ValueError("no scores")
            for s in scores:
                if not 0 <= s <= 1:
                    raise ValueError(f"bad score {s}")


        def summarise(scores):
            return sum(scores) / len(scores), max(scores), len(scores)


        def report(name, scores):
            validate_scores(scores)
            mean, best, n = summarise(scores)
            return f"{name}: mean {mean:.2f}, best {best:.2f}, n={n}"
        """,
        why="""Each small function now has one reason to change and can be tested and reused alone: `summarise` can feed a
        dashboard, `validate_scores` can guard other metrics. The loops became `sum` and `max`, and the range check became a
        chained comparison (1.1). Splitting is worth it when the pieces have names that explain them; a function you can
        only name `step2` is usually not a real job."""),
    predict("Unpacking a result that can be None", "medium",
        code="""
        def stats(xs):
            if not xs:
                return None
            return min(xs), max(xs), sum(xs) / len(xs)

        lo, hi, avg = stats([2, 4, 9])
        print(lo, hi, round(avg, 2))
        print(stats([]))
        try:
            lo, hi, avg = stats([])
        except TypeError as e:
            print("TypeError:", e)
        """,
        hints=["What happens when you try to unpack `None` into three names?"],
        why="""For real data the tuple unpacks fine. For an empty list the function returns `None`, and unpacking `None`
        raises `TypeError: cannot unpack non-iterable NoneType object`, far away from the cause. Returning different kinds of
        things from different paths pushes a check onto every caller. Alternatives: raise `ValueError` for empty input,
        or return a value of the same shape such as `(None, None, None)`, and document the choice."""),
    choose("A helper function inside a hot loop", "medium",
        prompt="Both sum the squares of a million numbers. Which is faster?",
        setup="""xs = list(range(1_000_000))
def square(x):
    return x * x""",
        options={
            "a": "total = sum(square(x) for x in xs)",
            "b": "total = sum(x * x for x in xs)",
        },
        answer="b",
        hints=["What extra work does every `square(x)` add, a million times over?"],
        why="""Each Python function call has a fixed cost: building a frame, binding the argument, returning. In A that cost
        is paid a million times for a one-multiplication body. B does the multiplication inline. Recent Pythons have made
        calls much cheaper, but not free. This is no reason to avoid functions in general (clarity wins almost everywhere),
        but in a tight loop over big data it is why numpy's whole-array operations (`(arr ** 2).sum()`) beat any per-item
        Python function by a wide margin."""),
    write("Build chat messages with keyword-only options", "medium", tag="GenAI",
        prompt="""Write `build_messages(question, *, system=None, history=(), context=None)` that returns a new list of
        chat messages in this order: an optional system message, the history messages, then the user message. If
        `context` is given, the user message content is `"Context:\\n{context}\\n\\nQuestion: {question}"`, otherwise just the
        question. `history` must not be changed.""",
        code="""
        def build_messages(question, *, system=None, history=(), context=None):
            pass
        """,
        tests="""
        h = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello!"}]
        out = build_messages("Refund time?", system="Be brief.", history=h, context="Refunds take 5 days.")
        assert out[0] == {"role": "system", "content": "Be brief."}
        assert out[1:3] == h and len(h) == 2
        assert out[3] == {"role": "user", "content": "Context:\\nRefunds take 5 days.\\n\\nQuestion: Refund time?"}
        assert build_messages("Hi") == [{"role": "user", "content": "Hi"}]
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        assert raises(TypeError, build_messages, "Hi", "Be brief.")
        """,
        hints=["Start with an empty list, add the parts in order, return it. `list(history)` makes a new list from the history.",
               "The last test passes `system` by position. The `*` in the signature is what makes that a `TypeError`."],
        solution="""
        def build_messages(question, *, system=None, history=(), context=None):
            messages = []
            if system is not None:
                messages.append({"role": "system", "content": system})
            messages.extend(history)
            content = f"Context:\\n{context}\\n\\nQuestion: {question}" if context is not None else question
            messages.append({"role": "user", "content": content})
            return messages
        """,
        why="""Keyword-only options make calls readable (`build_messages(q, context=c)`) and protect against mistakes: with
        three optional parameters, a positional call like `build_messages(q, "Be brief.")` would silently put a system
        prompt where history belongs. `history=()` is an immutable default (2.4), and `extend` copies the history's
        messages into a **new** list, so the caller's list is never changed. Checking `is not None` (not truthiness) means
        an empty-string system prompt is still sent, which is the caller's choice to make."""),
    write("Exponential backoff for API retries", "medium", tag="GenAI",
        prompt="""Write `backoff_delays(attempts, *, base=0.5, factor=2.0, cap=8.0)` that returns the list of wait times
        before each retry: `base`, `base * factor`, `base * factor ** 2`, and so on, each limited to `cap`. `attempts` is
        the number of retries; 0 gives `[]`.""",
        code="""
        def backoff_delays(attempts, *, base=0.5, factor=2.0, cap=8.0):
            pass
        """,
        tests="""
        assert backoff_delays(6) == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]
        assert backoff_delays(0) == []
        assert backoff_delays(3, base=1, factor=3, cap=5) == [1, 3, 5]
        assert backoff_delays(2, cap=0.2) == [0.2, 0.2]
        """,
        hints=["One comprehension: `min(cap, base * factor ** i)` for each `i` in `range(attempts)`."],
        solution="""
        def backoff_delays(attempts, *, base=0.5, factor=2.0, cap=8.0):
            return [min(cap, base * factor ** i) for i in range(attempts)]
        """,
        why="""Waiting longer after each failure stops your client from hammering an API that is already overloaded, and
        the cap keeps the wait from growing without limit. The tuning knobs are keyword-only with sensible defaults, so
        the usual call is just `backoff_delays(5)`. Real clients also add random **jitter** (`random.uniform(0, delay)`) so
        that many clients that failed at the same moment do not all retry at the same moment; libraries such as `tenacity`
        and the OpenAI and Anthropic SDKs do this for you."""),
)

section("hard", "Hard",
    write("Flatten nested JSON into columns", "hard", tag="Data work",
        prompt="""LLM extraction returns nested JSON, but the report needs flat columns. Write
        `flatten(obj, prefix="")` that returns a dict from dotted paths to plain values: dict keys join with `.`, list
        positions become numbers. Empty dicts and lists produce no columns.""",
        code="""
        def flatten(obj, prefix=""):
            pass
        """,
        tests="""
        data = {"id": 7, "customer": {"name": "Ana", "tier": "gold"}, "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}], "notes": []}
        assert flatten(data) == {
            "id": 7, "customer.name": "Ana", "customer.tier": "gold",
            "items.0.sku": "A1", "items.0.qty": 2, "items.1.sku": "B2", "items.1.qty": 1,
        }
        assert flatten(5) == {"": 5}
        assert flatten({"a": None}) == {"a": None}
        """,
        hints=["Recursive case: for each key (or index) and child, call `flatten(child, new_prefix)` and merge the result.",
               "Build `new_prefix` as `f\"{prefix}.{key}\"` when `prefix` is not empty, otherwise just `str(key)`."],
        solution="""
        def flatten(obj, prefix=""):
            if isinstance(obj, dict):
                pairs = obj.items()
            elif isinstance(obj, list):
                pairs = enumerate(obj)
            else:
                return {prefix: obj}
            out = {}
            for key, child in pairs:
                path = f"{prefix}.{key}" if prefix else str(key)
                out.update(flatten(child, path))
            return out
        """,
        why="""The function has one base case (a plain value becomes one column) and one recursive case that treats dicts and
        lists the same way by turning both into `(key, child)` pairs. That unification is what keeps it short. The
        default `prefix=""` is immutable and safe (2.4), and empty containers produce no pairs, so no columns. pandas has
        this built in as `pd.json_normalize`, which flattens dicts but keeps lists as values by default; knowing how to write
        it yourself helps when you need a different rule."""),
    fix("Read the code: an evaluation that stops early", "hard", tag="GenAI",
        prompt="""This scores an LLM's answers against gold answers for an evaluation run. It reports 100% accuracy on
        sets the model obviously gets wrong, and crashes on an empty set. Read the whole function, find both bugs, and fix
        them so it returns `{"accuracy": ..., "errors": [...]}` for any input.""",
        code="""
        def normalise(answer):
            return " ".join(answer.lower().split())


        def evaluate(predictions, gold):
            if len(predictions) != len(gold):
                raise ValueError("predictions and gold differ in length")
            correct = 0
            errors = []
            for i, (pred, ref) in enumerate(zip(predictions, gold)):
                if normalise(pred) == normalise(ref):
                    correct += 1
                else:
                    errors.append(i)
                return {"accuracy": correct / len(gold), "errors": errors}
        """,
        tests="""
        r = evaluate(["Paris", "4", " Blue  whale "], ["paris", "5", "blue whale"])
        assert r == {"accuracy": 2 / 3, "errors": [1]}
        assert evaluate(["x"], ["y"]) == {"accuracy": 0.0, "errors": [0]}
        assert evaluate([], []) == {"accuracy": 0.0, "errors": []}
        """,
        hints=["Look at the indentation of the `return`. How many items does the loop really check?",
               "When the lists are empty, the loop body never runs. What does the function return then, and what would the division do?"],
        solution="""
        def normalise(answer):
            return " ".join(answer.lower().split())


        def evaluate(predictions, gold):
            if len(predictions) != len(gold):
                raise ValueError("predictions and gold differ in length")
            if not gold:
                return {"accuracy": 0.0, "errors": []}
            correct = 0
            errors = []
            for i, (pred, ref) in enumerate(zip(predictions, gold)):
                if normalise(pred) == normalise(ref):
                    correct += 1
                else:
                    errors.append(i)
            return {"accuracy": correct / len(gold), "errors": errors}
        """,
        why="""The `return` is indented inside the loop, so the function returns after the **first** item: if that one is
        correct, the "accuracy" is `1 / len(gold)` at best, and here the first answer matched, so the reported number
        depended only on item 0. With an empty set the loop never runs, the function falls off the end and returns `None`;
        after moving the `return` out, it would divide by zero instead. The guard clause handles the empty case explicitly.
        An evaluation that looks better than reality is the most dangerous kind of bug in ML work, because nobody goes
        looking for it."""),
    predict("What a function object knows", "hard",
        code="""
        def score(a, b=2, *, c=3):
            "Add three numbers."
            return a + b + c

        print(score.__name__, "|", score.__doc__)
        print(score.__defaults__, score.__kwdefaults__)
        print(score.__code__.co_varnames[:score.__code__.co_argcount])
        score.__defaults__ = (10,)
        print(score(1))
        """,
        hints=["Positional defaults and keyword-only defaults are stored separately.",
               "`__defaults__` can be replaced. The next call uses whatever it holds."],
        why="""`__defaults__` holds positional defaults, `__kwdefaults__` the keyword-only ones. `co_argcount` counts the
        positional parameters (`a` and `b`, not the keyword-only `c`). Replacing `__defaults__` changes the default of `b`
        for every later call, so `score(1)` is `1 + 10 + 3`. That shows again that defaults are data stored on the function
        object (2.4), not something re-read from the source. You should never patch defaults in real code, but this is
        exactly the information tools read to describe a function."""),
    write("Call a tool with only the arguments it accepts", "hard", tag="GenAI",
        prompt="""LLMs often add extra fields when they call a tool. Write `call_with(fn, data)` that calls `fn` using
        only the keys of the dict `data` that match `fn`'s parameter names, passed as keyword arguments, and ignores the
        rest. If `fn` accepts `**kwargs`, pass everything. Missing required arguments must still raise `TypeError`, the
        normal Python way.""",
        code="""
        import inspect

        def call_with(fn, data):
            pass
        """,
        tests="""
        def raises(exc, f, *args):
            try:
                f(*args)
            except exc:
                return True
            return False
        def search(query, k=5):
            return f"{query}:{k}"
        assert call_with(search, {"query": "refunds", "k": 3, "reason": "the user asked"}) == "refunds:3"
        assert call_with(search, {"query": "refunds"}) == "refunds:5"
        assert raises(TypeError, call_with, search, {"k": 3})
        def log_all(**fields):
            return sorted(fields)
        assert call_with(log_all, {"a": 1, "b": 2}) == ["a", "b"]
        """,
        hints=["`inspect.signature(fn).parameters` maps names to parameter objects. A parameter's `.kind` tells you whether it is `VAR_KEYWORD` (`**kwargs`).",
               "Keep a key if its name is in the parameters. Then call `fn(**kept)` and let Python raise for anything missing."],
        solution="""
        import inspect

        def call_with(fn, data):
            params = inspect.signature(fn).parameters
            if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
                return fn(**data)
            kept = {k: v for k, v in data.items() if k in params}
            return fn(**kept)
        """,
        why="""The signature is read from the function object itself, so the same `call_with` works for any tool without
        a list of allowed fields. Filtering extra keys tolerates harmless LLM noise (a `"reason"` field), while a missing
        required argument still fails loudly, because the call itself is a normal Python call. This is a simplified
        version of what FastAPI does for request parameters and what agent frameworks do for tools. Real versions also
        validate types from the annotations (Pydantic), and should **log** dropped keys, since a dropped key can also be a
        misspelled real argument."""),
)

section("interview", "Interview questions",
    explain("What does a function return without a `return` statement, and how does that cause bugs?", "medium", tag="Interview",
        why="""It returns `None`, and so does a bare `return`. Bugs come from paths that forget to return: an `if/elif`
        chain without a final `return`, an expression written where a `return` was meant, or a `return` indented inside a
        loop so it exits early. The `None` then travels far from its cause and fails later, as `TypeError: cannot unpack
        non-iterable NoneType object` or a silently wrong metric. Prevent it by ending every function with an explicit return
        for the default case, using guard clauses, returning the same kind of value on every path, and letting a type checker
        (mypy, pyright) flag `Optional` results that are not checked (Module 11)."""),
    explain("Recursion or a loop in Python: how do you choose?", "medium", tag="Interview",
        why="""Recursion is natural for nested or tree-shaped data of moderate depth: JSON documents, file trees, parse trees,
        divide-and-conquer algorithms. But CPython limits recursion depth (1,000 by default), does not optimise tail calls,
        and every call has overhead, so deep recursion raises `RecursionError` and long recursions are slower than loops.
        Use a loop for linear repetition, and an explicit stack (a list you push and pop) to walk very deep trees
        iteratively. Mention that `sys.setrecursionlimit` exists but only moves the problem, and that `functools.cache`
        makes recursive solutions with repeated subproblems fast (dynamic programming, Module 16)."""),
    explain("How does a framework like FastAPI know which query parameters your endpoint takes?", "hard", tag="Interview",
        why="""Functions are objects that describe themselves. When you register an endpoint, FastAPI calls
        `inspect.signature` on your function and reads each parameter's name, its default, and its type annotation. A
        parameter with a default becomes an optional query parameter, one without becomes required, and the annotation (for
        example `int` or a Pydantic model) tells it how to parse and validate the incoming value, which also generates the
        OpenAPI docs. Nothing runs your function until a request arrives. Mention that the same idea powers agent tools:
        the signature and docstring of a Python function become the JSON schema the LLM sees, which is why docstrings and
        type hints matter in GenAI code."""),
)

recap(
    "`def` runs: it builds a function object and binds the name. Old references keep the old function.",
    "Arguments fill parameters by position, then by name, then from defaults. The four `TypeError` messages (missing, too many, multiple values, unexpected) tell you exactly which rule broke.",
    "Every path should end in an explicit `return`. Use guard clauses, and return the same kind of value from every path.",
    "Function objects carry their docstring, defaults and signature. FastAPI and agent frameworks read them to call your code.",
    "Recursion suits nested data of moderate depth: cover every base case (including empty containers), and use a loop for deep or long repetition.",
)
